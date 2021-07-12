import json

import pulumi
from pulumi_aws import cloudformation, docdb, ec2, kms, route53

from generic_secuity_groups import ALLOW_ALL_TRAFFIC_FROM_BASTION, ALLOW_ALL_EGRESS_TRAFFIC
from secrets import create_raw_json_secret
from utils import get_resource_name_by_convention, get_lightlytics_com_route53_zone, \
    get_route53_record_name_by_convention

config = pulumi.Config()

MONGO_PASSWORD_PLACEHOLDER = "MONGO_PASSWORD_PLACEHOLDER"


def create_mongodb_cft_cluster(vpc, private_subnets, bastion, keypair, eks):
    mongo_user, mongo_password = create_mongodb_credentials()
    name, tags = get_resource_name_by_convention("mongodb")
    with open('CloudFormation/mongo/mongodb.template') as f:
        mongo_template_body = f.read()

    mongodb = cloudformation.Stack(
        name,
        tags=tags,
        template_body=mongo_template_body,
        parameters={
            "VPC": vpc.id,
            "PrimaryNodeSubnet": private_subnets[0].id,
            "Secondary0NodeSubnet": private_subnets[1].id,
            "Secondary1NodeSubnet": private_subnets[0].id,
            "BastionSecurityGroupID": bastion.outputs['BastionSecurityGroupID'],
            "EKSSecurityGroupID": eks.vpc_config.cluster_security_group_id,
            "KeyPairName": keypair.key_name,
            "MongoDBAdminUsername": mongo_user,
            "MongoDBAdminPassword": mongo_password
        },
        capabilities=['CAPABILITY_IAM'],
        # We must place it here since pulumi thinks we change everytime of cloud formation NoEcho field.
        opts=pulumi.ResourceOptions(ignore_changes=["parameters", "templateBody"])
    )

    _create_mongodb_dns_records(mongodb.outputs)
    pulumi.export("mongodb", mongodb.outputs)
    return mongodb.outputs


# TODO : fix it - run on the output array
def _create_mongodb_dns_records(mongodb_cft_output):
    zone = get_lightlytics_com_route53_zone()
    stack_name = pulumi.get_stack()
    # Primary server
    name, _ = get_route53_record_name_by_convention(f"{stack_name}-mongodb_primary_dns_record", "A")
    mongodb_primary_dns_record = route53.Record(
        name,
        zone_id=zone.zone_id,
        name=f"{stack_name}-mongo-primary",
        type="A",
        ttl=300,
        records=[mongodb_cft_output['PrimaryReplicaNodeIp']]
    )

    # Secondary records
    name, _ = get_route53_record_name_by_convention(f"{stack_name}-mongodb_secondary_0_dns_record", "A")
    mongodb_secondary_0_dns_record = route53.Record(
        name,
        zone_id=zone.zone_id,
        name=f"{stack_name}-mongodb-secondary-0",
        type="A",
        ttl=300,
        records=[mongodb_cft_output['SecondaryReplicaNode0Ip']]
    )

    name, _ = get_route53_record_name_by_convention(f"{stack_name}-mongodb_secondary_1_dns_record", "A")
    mongodb_secondary_1_dns_record = route53.Record(
        name,
        zone_id=zone.zone_id,
        name=f"{stack_name}-mongodb-secondary-1",
        type="A",
        ttl=300,
        records=[mongodb_cft_output['SecondaryReplicaNode1Ip']]
    )
    mongodb_records = pulumi.Output.all(
        mongodb_primary_dns_record.fqdn,
        mongodb_secondary_0_dns_record.fqdn,
        mongodb_secondary_1_dns_record.fqdn).apply(lambda l: f"{l[0]},{l[1]},{l[2]}")
    pulumi.export("mongodb_dns_records", mongodb_records)

# Changes to a DocDB Cluster can occur when you manually change a parameter, such as port, and are reflected in the
# next maintenance window. Because of this, this provider may report a difference in its planning phase because a
# modification has not yet taken place. You can use the apply_immediately flag to instruct the service to apply the
# change immediately (see documentation below). Note: using apply_immediately can result in a brief downtime as the
# server reboots. Note: All arguments including the username and password will be stored in the raw state as
# plain-text.
# You can only create an Amazon DocumentDB cluster in an Amazon Virtual Private Cloud (Amazon VPC) that
# spans three Availability Zones. Each Availability Zone must contain at least one subnet
def _create_docdb_cluster_subnet_groups(vpc, private_subnets):
    name, tags = get_resource_name_by_convention("document_db_subnet_group")
    return docdb.SubnetGroup(name,
                             name=name,
                             description="subnet group to use in document db",
                             subnet_ids=[subnet.id for subnet in private_subnets],
                             tags=tags)


def _create_docdb_cluster_security_groups(vpc, security_groups, eks):
    name, tag = get_resource_name_by_convention("sg_document_db")
    return [
        ec2.SecurityGroup(
            name,
            vpc_id=vpc.id,
            name=name,
            tags=tag,
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="Access From EKS",
                    from_port=27017,
                    to_port=27017,
                    protocol="tcp",
                    security_groups=[eks.vpc_config.cluster_security_group_id]
                ),
            ]),
        security_groups[ALLOW_ALL_TRAFFIC_FROM_BASTION],
        security_groups[ALLOW_ALL_EGRESS_TRAFFIC]
    ]


def _create_docdb_cluster_parameter_group():
    name, tags = get_resource_name_by_convention("document-db-parameter-group")
    return docdb.ClusterParameterGroup(name,
                                       name=name,
                                       description="docdb cluster parameter group - NO TLS - REPLACE THIS LATER!",
                                       family="docdb4.0",
                                       parameters=[docdb.ClusterParameterGroupParameterArgs(
                                           name="tls",
                                           value="disabled",
                                       )])


def create_mongodb_docdb(vpc, private_subnets, security_groups, eks):
    doc_db_subnet_group = _create_docdb_cluster_subnet_groups(vpc, private_subnets)
    doc_db_security_groups = _create_docdb_cluster_security_groups(vpc, security_groups, eks)
    doc_db_parameter_groups = _create_docdb_cluster_parameter_group()
    name, tags = get_resource_name_by_convention("document-db")
    # MasterUsername admin cannot be used as it is a reserved word used by the engine
    mongo_user, mongo_password = create_mongodb_credentials(admin_user="mongoadmin", secret_name="docdb_secret")
    cluster = docdb.Cluster(name,
                            tags=tags,
                            db_cluster_parameter_group_name=doc_db_parameter_groups.name,
                            db_subnet_group_name=doc_db_subnet_group.name,
                            vpc_security_group_ids=doc_db_security_groups,
                            backup_retention_period=7,
                            cluster_identifier=name,
                            engine="docdb",
                            storage_encrypted=True,
                            # aws default encryption key...
                            kms_key_id=kms.get_key(key_id="alias/aws/rds").arn,
                            engine_version="4.0.0",
                            master_password=mongo_password,
                            master_username=mongo_user,
                            preferred_backup_window="07:00-09:00",
                            preferred_maintenance_window="Sun:11:00-Sun:13:00",
                            skip_final_snapshot=True)

    _create_docdb_cluster_instances(cluster, private_subnets)


def _create_docdb_cluster_instances(cluster, private_subnets):
    cluster_instances = []
    for i, _ in enumerate(private_subnets):
        # only lowercase alphanumeric characters and hyphens allowed in "identifier"
        name, tag = get_resource_name_by_convention("document-db-instance")
        name = f"{name}-{i + 1}"
        cluster_instances.append(docdb.ClusterInstance(name,
                                                       tags=tag,
                                                       identifier=name,
                                                       cluster_identifier=cluster.id,
                                                       instance_class="db.r5.2xlarge"))


def create_mongodb_credentials(admin_user="admin", secret_name="mongo_top_secret"):
    mongo_password = config.require_secret('mongoDbPassword')
    mongo_credentials_serialized = json.dumps({
        "username": admin_user,
        "password": MONGO_PASSWORD_PLACEHOLDER
    })
    # We need this since this is the way to contact secrets in Pulumi (you can't just add to string/object)
    temp = mongo_credentials_serialized.split(MONGO_PASSWORD_PLACEHOLDER)
    mongo_credentials = pulumi.Output.concat(temp[0], mongo_password, temp[1])
    create_raw_json_secret(secret_name, mongo_credentials)
    return admin_user, mongo_password
