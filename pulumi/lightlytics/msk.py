import pulumi
from pulumi_aws import msk, ec2

from utils import get_resource_name_by_convention


def _create_msk_cluster_configuration():
    name, _ = get_resource_name_by_convention("kafka-cluster-conf")
    return msk.Configuration(name,
                             name=name,
                             kafka_versions=["2.6.0"],
                             server_properties=
                             """
                             auto.create.topics.enable=true
                             """)


def create_msk(private_subnets, vpc, eks):
    msk_conf = _create_msk_cluster_configuration()
    kafka_security_group = create_msk_security_group(eks, vpc)
    name, tag = get_resource_name_by_convention("kafka-cluster")
    kafka_cluster = msk.Cluster(
        name,
        tags=tag,
        cluster_name=name,
        configuration_info=msk.ClusterConfigurationInfoArgs(
            arn=msk_conf.arn,
            revision=msk_conf.latest_revision
        ),
        kafka_version="2.6.0",
        number_of_broker_nodes=2,
        encryption_info=msk.ClusterEncryptionInfoArgs(
            encryption_in_transit=msk.ClusterEncryptionInfoEncryptionInTransitArgs(
                in_cluster=True,
                client_broker='TLS_PLAINTEXT'
            )
        ),
        broker_node_group_info=msk.ClusterBrokerNodeGroupInfoArgs(
            instance_type="kafka.m5.large",
            ebs_volume_size=1000,
            client_subnets=private_subnets[:2],
            security_groups=[kafka_security_group.id]
        )
    )
    pulumi.export("kafka_cluster_brokers_tls", kafka_cluster.bootstrap_brokers_tls)
    pulumi.export("kafka_cluster_brokers_plaintext", kafka_cluster.bootstrap_brokers)
    return kafka_cluster


def create_msk_security_group(eks, vpc):
    # To access your Amazon MSK cluster from a client that's in the same Amazon VPC as the cluster, make sure the
    # cluster's security group has an inbound rule that accepts traffic from the client's security group.
    name, tag = get_resource_name_by_convention("kafka_security_group")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag,
        ingress=[
            ec2.SecurityGroupIngressArgs(
                description="EKS Ingress Rule",
                from_port=0,
                to_port=0,
                protocol=-1,
                security_groups=[
                    eks.vpc_config.cluster_security_group_id
                ]
            )
        ],
        egress=[
            ec2.SecurityGroupEgressArgs(
                description="MSK Egress Rule",
                from_port=0,
                to_port=0,
                protocol=-1,
                cidr_blocks=["0.0.0.0/0"]
            )
        ])
