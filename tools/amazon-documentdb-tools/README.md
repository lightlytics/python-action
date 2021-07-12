# Amazon DocumentDB Tools

This repo contains tools to make migrating to Amazon DocumentDB (with MongoDB compatibility) easier.

## Amazon DocumentDB Index Tool

The `DocumentDB Index Tool` makes it easier to migrate only indexes (not data) between a source MongoDB deployment and a
Amazon DocumentDB cluster. The Index Tool can also help you find potential compatibility issues between your source
databases and Amazon DocumentDB. You can use the Index Tool to dump indexes and database metadata, or you can use the
tool against an existing dump created with the mongodump tool.

For more information about this tool, checkout the [Amazon DocumentDB Index Tool README](./index-tool/README.md) file.

## Cosmos DB Migration Utility

The `Cosmos DB Migration Utility` is an application created to help live migrate the Azure Cosmos DB for MongoDB API
databases to Amazon DocumentDB with very little downtime. It keeps the target Amazon DocumentDB cluster in sync with the
source Microsoft Azure Cosmos DB until the client applications are cut over to the DocumentDB cluster.

For more information about the Cosmos DB Migrator tool, checkout
the [Cosmos DB Migration Utility README](./cosmos-db-migration-utility/README.md) file.

## Using the Index Tool

To dump indexes from a running MongoDB instance or replica set, run the following command:
`python migrationtools/documentdb_index_tool.py --host 127.0.0.1 --port 2461 --username admin --password <PASSWORD> --auth-db admin --dir mongodb-meta --dump-indexes`

To check for compatibility issues against dumped database metadata, run the following command:
`python migrationtools/documentdb_index_tool.py --show-issues --dir <directory that contains metadata dump>`

To restore only indexes that are compatible with Amazon DocumentDB, run the following command:
`python migrationtools/documentdb_index_tool.py --host 127.0.0.1 --port 2461 --username mongoadmin --password <PASSWORD> --restore-indexes --dir mongodb-meta`

## MongodbDump

```shell
mongodump --uri="mongodb://admin:PASSWORD@127.0.0.1:2461/?authSource=admin&readPreference=primary"  --db cust_5fe08b93fb6c7678a49a96a3 --excludeCollection=flowlogs_raw --out dump
mongodump --uri="mongodb://admin:PASSWORD@127.0.0.1:2461/?authSource=admin&readPreference=primary"  --db lightlytics --out dump
```

## MongoRestore

```shell
mongorestore --uri="mongodb://admin:PASSWORD@127.0.0.1:2461/?authSource=admin&readPreference=primary"  --db=lightlytics dump/lightlytics
mongorestore --uri="mongodb://admin:PASSWORD@127.0.0.1:2461/?authSource=admin&readPreference=primary"  --db=cust_5fe08b93fb6c7678a49a96a3 dump/cust_5fe08b93fb6c7678a49a96a3
```
or
```shell
mongorestore --host="127.0.0.1:2461" --username=mongoadmin --password=PASSWORD --db=lightlytics dump/lightlytics
mongorestore --host="127.0.0.1:2461" --username=mongoadmin --password=PASSWORD --db=cust.... dump/lightlytics
```

