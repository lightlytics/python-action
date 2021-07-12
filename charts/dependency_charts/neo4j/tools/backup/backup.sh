#!/bin/bash

if [ -z $NEO4J_ADDR ] ; then
    echo "You must specify a NEO4J_ADDR env var with port, such as my-neo4j:6362"
    exit 1
fi

if [ -z $DATABASE ] ; then
    echo "You must specify a DATABASE env var; comma-separated list of databases to backup, such as neo4j,system"
    exit 1
fi

if [ -z $BUCKET ]; then
    echo "You must specify a BUCKET address such as gs://my-backups/"
    exit 1
fi

if [ -z $HEAP_SIZE ] ; then
    export HEAP_SIZE=2G
fi

if [ -z $PAGE_CACHE ]; then
    export PAGE_CACHE=2G
fi

if [ -z $FALLBACK_TO_FULL ] ; then
    export FALLBACK_TO_FULL="true"
fi

if [ -z $CHECK_CONSISTENCY ] ; then
    export CHECK_CONSISTENCY="true"
fi

if [ -z $CHECK_INDEXES ] ; then
    export CHECK_INDEXES="true"
fi

if [ -z $CHECK_GRAPH ] ; then
    export CHECK_GRAPH="true"
fi

if [ -z $CHECK_LABEL_SCAN_STORE ] ; then
    export CHECK_LABEL_SCAN_STORE="true"
fi

if [ -z $CHECK_PROPERTY_OWNERS ] ; then
    export CHECK_PROPERTY_OWNERS="false"
fi

if [ -z $GOOGLE_APPLICATION_CREDENTIALS ] ; then
    echo "Setting default google credential location to /auth/credentials.json"
    export GOOGLE_APPLICATION_CREDENTIALS=/auth/credentials.json
fi

# This function takes a file and
# (a) uploads it to BUCKET
# (b) updates the latest pointer
function cloud_copy {
    full_path=$1
    database=$2

    # Trim trailing slash from BUCKET if it's there, because it messes up the
    # copy commands if you copy gs://a//foo to gs://a//bar (double slash in path)
    # https://stackoverflow.com/a/17542946/2920686
    if [ "${BUCKET: -1}" = "/" ]; then
        BUCKET="${BUCKET%?}"
    fi

    # Want bucket_and_path *without* a final slash, so we can add it ourselves and
    # know what's a file and what's a directory.
    bucket_and_path=""
    if [ "${BUCKET: -1}" = "/" ]; then
        bucket_and_path="${BUCKET%?}"
    else 
        bucket_and_path=$BUCKET
    fi

    echo "Pushing $full_path -> $bucket_and_path"

    # Terminating slash is important to create correct filename.
    gsutil cp "$full_path" "$bucket_and_path/"

    backup="$bucket_and_path/$BACKUP_SET.tar.gz"
    latest="$bucket_and_path/$LATEST_POINTER"

    echo "Updating latest backup pointer $backup -> $latest"
    gsutil cp "$backup" "$latest"
}

function backup_database {   
    db=$1

    export BACKUP_SET="$db-$(date "+%Y-%m-%d-%H:%M:%S")"
    export LATEST_POINTER="$db-latest.tar.gz"

    echo "=============== BACKUP $db ==================="
    echo "Beginning backup from $NEO4J_ADDR to /data/$BACKUP_SET"
    echo "Using heap size $HEAP_SIZE and page cache $PAGE_CACHE"
    echo "FALLBACK_TO_FULL=$FALLBACK_TO_FULL, CHECK_CONSISTENCY=$CHECK_CONSISTENCY"
    echo "CHECK_GRAPH=$CHECK_GRAPH CHECK_INDEXES=$CHECK_INDEXES"
    echo "CHECK_LABEL_SCAN_STORE=$CHECK_LABEL_SCAN_STORE CHECK_PROPERTY_OWNERS=$CHECK_PROPERTY_OWNERS"
    echo "To google storage bucket $BUCKET using credentials located at $GOOGLE_APPLICATION_CREDENTIALS"
    echo "============================================================"

    neo4j-admin backup \
        --from="$NEO4J_ADDR" \
        --backup-dir=/data \
        --database=$db \
        --pagecache=$PAGE_CACHE \
        --fallback-to-full=$FALLBACK_TO_FULL \
        --check-consistency=$CHECK_CONSISTENCY \
        --check-graph=$CHECK_GRAPH \
        --check-indexes=$CHECK_INDEXES \
        --check-label-scan-store=$CHECK_LABEL_SCAN_STORE \
        --check-property-owners=$CHECK_PROPERTY_OWNERS \
        --verbose

    # Docs: see exit codes here: https://neo4j.com/docs/operations-manual/current/backup/performing/#backup-performing-command
    backup_result=$?
    case $backup_result in
        0) echo "Backup succeeded - $db" ;;
        1) echo "Backup FAILED - $db" ;;
        2) echo "Backup succeeded but consistency check failed - $db" ;;
        3) echo "Backup succeeded but consistency check found inconsistencies - $db" ;; 
    esac

    if [ $backup_result -eq 1 ] ; then
        echo "Aborting other actions; backup failed"
        exit 1
    fi

    echo "Backup size:"
    du -hs "/data/$db"

    echo "Final Backupset files"
    ls -l "/data/$db"

    echo "Archiving and Compressing -> /data/$BACKUP_SET.tar"

    tar -zcvf "/data/$BACKUP_SET.tar.gz" "/data/$db" --remove-files

    if [ $? -ne 0 ] ; then
       echo "BACKUP ARCHIVING OF $db FAILED"
       exit 1
    fi

    echo "Zipped backup size:"
    du -hs "/data/$BACKUP_SET.tar.gz"

    cloud_copy "/data/$BACKUP_SET.tar.gz"

    if [ $? -ne 0 ] ; then
       echo "Storage copy of backup for $db FAILED"
       exit 1
    fi
}

######################################################

echo "Activating google credentials before beginning"
gcloud auth activate-service-account --key-file "$GOOGLE_APPLICATION_CREDENTIALS"

if [ $? -ne 0 ] ; then
    echo "Credentials failed; no way to copy to google."
    echo "Ensure GOOGLE_APPLICATION_CREDENTIALS is appropriately set."
fi

# Split by comma
IFS=","
read -a databases <<< "$DATABASE"
for db in "${databases[@]}"; do  
   backup_database "$db"
done

echo "All finished"
exit 0
