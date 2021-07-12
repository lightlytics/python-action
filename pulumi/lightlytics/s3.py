import re

import pulumi
from pulumi_aws import s3, Provider

conf = pulumi.Config()

from utils import get_resource_name_by_convention

ARTIFACTS_BUCKET = "artifacts"
CFT_PUBLIC_BUCKET = "public-cloudformation"
FLOW_LOGS_DOG_FOOD = "flow-logs-dogfood"
MONGODB_BACKUPS_BUCKET = "mongodb-backups"
PUBLIC_OBJECT_READ_FOR_BUCKET = "bucket_policy_public_object_access.json"
PLACE_HOLDER_FOR_BUCKET_NAME = "PLACE_HOLDER_FOR_BUCKET_NAME"


# todo(zeev+dan): check if we need bucket policy for the artifact bucket


def create_flow_logs_dog_food_bucket():
    buckets_conf = [{
        "name": FLOW_LOGS_DOG_FOOD, "acl": None, "policy": None
    }]
    created_buckets = _create_s3_buckets(buckets_conf)
    _block_all_public_access_to_buckets(buckets_conf, created_buckets)


def create_mongodb_backups_bucket():
    buckets_conf = [{
        "name": MONGODB_BACKUPS_BUCKET, "acl": None, "policy": None
    }]
    created_buckets = _create_s3_buckets(buckets_conf)
    _block_all_public_access_to_buckets(buckets_conf, created_buckets)
    return created_buckets[0]


def create_s3_cft_and_artifacts_buckets():
    buckets_conf = [
        {"name": ARTIFACTS_BUCKET, "acl": None, "policy": PUBLIC_OBJECT_READ_FOR_BUCKET},
        {"name": CFT_PUBLIC_BUCKET, "acl": None, "policy": None}
    ]
    created_buckets = _create_s3_buckets(buckets_conf)
    _allow_s3_buckets_public_access_to_objects(buckets_conf, created_buckets)

    output_buckets = {}
    for i, bucket in enumerate(buckets_conf):
        output_buckets[bucket["name"]] = created_buckets[i]
    return output_buckets


def create_region_external_s3_artifact_buckets():
    buckets = []
    regions = conf.require_object('externalRegions')
    regions.append(conf.require('primaryRegion'))
    for region in regions:
        provider = Provider(f's3-{region}-provider', region=region, profile="prod")
        bucket_conf = {"name": f'{ARTIFACTS_BUCKET}-{region}', "acl": None, "policy": PUBLIC_OBJECT_READ_FOR_BUCKET}
        name, tags = get_resource_name_by_convention(f'{ARTIFACTS_BUCKET}-{region}')
        policy = _handle_bucket_policy(name, bucket_conf)
        created_bucket = s3.Bucket(
            name,
            bucket=name,
            acl=bucket_conf.get('acl'),
            versioning=s3.BucketVersioningArgs(
                enabled=True,
            ),
            server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
                rule=
                s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=
                    s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )
            ),
            policy=policy,
            opts=pulumi.ResourceOptions(provider=provider)
        )
        buckets.append(created_bucket)
        pulumi.export(name, created_bucket.arn)
    return buckets


def _create_s3_buckets(buckets_conf):
    buckets = []
    for bucket_conf in buckets_conf:
        name, tags = get_resource_name_by_convention(bucket_conf['name'])
        policy = None
        if bucket_conf.get('policy'):
            policy = _handle_bucket_policy(name, bucket_conf)
        created_bucket = s3.Bucket(name,
                                   bucket=name,
                                   tags=tags,
                                   versioning=s3.BucketVersioningArgs(
                                       enabled=True,
                                   ),
                                   server_side_encryption_configuration=s3.BucketServerSideEncryptionConfigurationArgs(
                                       rule=
                                       s3.BucketServerSideEncryptionConfigurationRuleArgs(
                                           apply_server_side_encryption_by_default=
                                           s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                                               sse_algorithm="AES256"
                                           )
                                       )
                                   ),
                                   acl=bucket_conf.get('acl'),
                                   policy=policy)
        buckets.append(created_bucket)
        pulumi.export(name, created_bucket.arn)
    return buckets


def _allow_s3_buckets_public_access_to_objects(buckets_conf, created_buckets):
    for i, bucket in enumerate(created_buckets):
        name, _ = get_resource_name_by_convention(f"{buckets_conf[i]['name']}-public_access_block")
        s3.BucketPublicAccessBlock(
            name,
            bucket=bucket.id,
            restrict_public_buckets=True
        )


def _block_all_public_access_to_buckets(buckets_conf, created_buckets):
    for i, bucket in enumerate(created_buckets):
        name, _ = get_resource_name_by_convention(f"{buckets_conf[i]['name']}-public_access_block")
        s3.BucketPublicAccessBlock(
            name,
            bucket=bucket.id,
            restrict_public_buckets=True,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True
        )


def _handle_bucket_policy(bucket_full_name, buckets_conf):
    if buckets_conf['policy'] == PUBLIC_OBJECT_READ_FOR_BUCKET:
        return _grant_public_access_to_bucket_objects(bucket_full_name, buckets_conf)


def _grant_public_access_to_bucket_objects(bucket_full_name, buckets_conf):
    with open(f'./polices/{PUBLIC_OBJECT_READ_FOR_BUCKET}') as f:
        policy_document = f.read()
        file_split = re.split(f"{PLACE_HOLDER_FOR_BUCKET_NAME}", policy_document)
        policy = pulumi.Output.concat(file_split[0], bucket_full_name, file_split[1])
        return policy
