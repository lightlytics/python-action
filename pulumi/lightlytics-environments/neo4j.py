import json

import pulumi
from pulumi_aws import cloudformation, route53

from secrets import create_raw_json_secret
from utils import get_resource_name_by_convention, get_lightlytics_com_route53_zone,\
    get_route53_record_name_by_convention

config = pulumi.Config()

NEO4J_PASSWORD_PLACEHOLDER = "NEO4J_PASSWORD_PLACEHOLDER"


def create_neo4j(vpc, private_subnets, keypair, bastion, eks):
    name, tags = get_resource_name_by_convention('neo4jcft')
    neo4j_password = config.require_secret('neo4jPassword')
    neo4j_credentials_serialized = json.dumps({
        "username": "neo4j",
        "password": NEO4J_PASSWORD_PLACEHOLDER
    })
    temp = neo4j_credentials_serialized.split(NEO4J_PASSWORD_PLACEHOLDER)
    neo4j_credentials = pulumi.Output.concat(temp[0], neo4j_password, temp[1])
    create_raw_json_secret("neo4j_server_top_secret", neo4j_credentials)

    with open('CloudFormation/neo4j/neo4j.template') as f:
        neo4j_template_body = f.read()

    neo4j = cloudformation.Stack(
        "neo4j",
        template_body=neo4j_template_body,
        name=name,
        parameters={
            "VPC": vpc.id,
            "PrimaryNodeSubnet": private_subnets[0].id,
            "SecondaryNodeSubnet": private_subnets[1].id,
            "NetworkWhitelist": "0.0.0.0/0",
            "SSHKeyName": keypair.key_name,
            "EksSecurityGroupID": eks.vpc_config.cluster_security_group_id,
            "BastionSecurityGroupID": bastion.outputs['BastionSecurityGroupID'],
            "Password": neo4j_password
        },
        capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
        # We must place it here since pulumi thinks we change everytime of cloud formation NoEcho field.
        opts=pulumi.ResourceOptions(ignore_changes=["parameters", "templateBody"]),
        tags=tags
    )
    pulumi.export('neo4j', neo4j.outputs)
    _create_neo4j_dns_records(neo4j.outputs)
    return neo4j


def _create_neo4j_dns_records(neo4j_cft_output):
    zone = get_lightlytics_com_route53_zone()
    stack_name = pulumi.get_stack()
    all_records = []
    for core_index in range(3):
        name, _ = get_route53_record_name_by_convention(f"{stack_name}-neo4j_core{core_index}_primary_dns_record", "A")
        route53.Record(
            name,
            zone_id=zone.zone_id,
            name=f"{stack_name}-neo4j-core{core_index}",
            type="A",
            ttl=300,
            records=[neo4j_cft_output[f'Node{core_index}Ip']]
        )
        all_records.append(neo4j_cft_output[f'Node{core_index}Ip'])

    name, _ = get_route53_record_name_by_convention(f"neo4j-{stack_name}-cluster", "A")
    neo4j_dns_record = route53.Record(
        name,
        zone_id=zone.zone_id,
        name=f"neo4j-{stack_name}-cluster",
        type="A",
        ttl=300,
        records=all_records
    )

    pulumi.export("neo4j_dns_record", neo4j_dns_record.fqdn)




