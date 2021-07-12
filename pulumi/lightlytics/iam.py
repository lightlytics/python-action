import json
import re

import pulumi
from pulumi_aws import iam

from utils import get_resource_name_by_convention, create_eks_oidc_thumbprint

PLACE_HOLDER_FOR_OIDC_ARN = "PLACE_HOLDER_FOR_OIDC_ARN"
PLACE_HOLDER_FOR_OIDC_URL_WITH_AUD_SUFFIX = "PLACE_HOLDER_FOR_OIDC_URL_WITH_AUD_SUFFIX"
PLACE_HOLDER_FOR_OIDC_URL_WITH_SUB_SUFFIX = "PLACE_HOLDER_FOR_OIDC_URL_WITH_SUB_SUFFIX"
PLACE_HOLDER_FOR_OIDC_SERVICE_ACCOUNT_SUB = "PLACE_HOLDER_FOR_OIDC_SERVICE_ACCOUNT_SUB"
ASSUME_ROLE_POLICY_KEY = 'assume_role_policy'


# todo(zeev+dan): why there is no ALBIngressControllerIAMPolicy?

def create_iam(public_cloudformation_bucket, mongo_backups_bucket):
    created_iam_policies = create_lightlytics_iam_policies()
    # EKS CLUSTER OIDC CONNECT PROVIDER
    created_iam_policies["s3_iam_policy"] = create_iam_policy_write_access_to_bucket(public_cloudformation_bucket,
                                                                                     "cft")
    created_iam_policies["s3_iam_mongo_policy"] = create_iam_policy_write_access_to_bucket(mongo_backups_bucket,
                                                                                           "mongo")

    return created_iam_policies


def create_lightlytics_iam_policies():
    iam_polices_to_create = [
        {'name': 'sts_policy', 'file': 'polices/sts_assume_role_policy.json',
         'description': "sts policy for getting permissions to other accounts"},
        {'name': 'describe_regions_policy', 'file': 'polices/describe_regions_policy.json',
         'description': "describe regions policy for get all available regions"},
        {'name': 'ses_policy', 'file': 'polices/ses_policy.json',
         'description': "send emails policy"},
        {'name': 'sqs_policy', 'file': 'polices/sqs_policy.json',
         'description': "create and delete sqs queues policy"},
        {'name': 'sqs_messages_policy', 'file': 'polices/sqs_messages_policy.json',
         'description': "receive and delete messages from sqs"},
        {'name': 'external_dns_policy', 'file': 'polices/external_dns_policy.json',
         'description': "access to route53 in order to create DNS entries"},
        {'name': 'alb_ingress_controller_policy', 'file': 'polices/alb_ingress_controller_policy.json',
         'description': "policy for alb ingress k8s service"},
        {'name': 'secret_manager_policy', 'file': 'polices/secret_manager_policy.json',
         'description': "policy for k8s external secret manager"},
        {'name': "ssm_policy", 'file': 'polices/ssm_policy.json',
         'description': "policy for k8s external secret manager"},
    ]
    created_iam_policies = {}
    for i, policy in enumerate(iam_polices_to_create):
        with open(policy['file']) as f:
            name = policy['name']
            resource_name, _ = get_resource_name_by_convention(name)
            policy_file = json.load(f)
            created_policy = iam.Policy(
                resource_name,
                description=policy['description'],
                policy=json.dumps(policy_file)
            )
            created_iam_policies[name] = created_policy
    return created_iam_policies


def create_iam_policy_write_access_to_bucket(bucket, policy_name_suffix):
    name, _ = get_resource_name_by_convention(f's3_write_access_iam_policy-{policy_name_suffix}')
    s3_write_access_iam_policy = iam.Policy(
        name,
        description="Write Access to a given bucket arn",
        policy=bucket.arn.apply(
            lambda bucket_arn: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:PutObjectAcl"
                            ],
                            "Resource": f"{bucket_arn}/*"
                        }
                    ]
                }
            )
        ),
        opts=pulumi.ResourceOptions(ignore_changes=["description"]),
    )
    return s3_write_access_iam_policy
