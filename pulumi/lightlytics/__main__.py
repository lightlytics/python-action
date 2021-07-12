"""An AWS Python Pulumi program"""

# todo: protect resources against deletion?
# todo: secrets - https://www.pulumi.com/docs/intro/concepts/programming-model/#secrets
# todo: Jenkins
import pulumi

from access_token import create_access_token
from bastion import create_bastion
from ecr import create_ecr
from generic_secuity_groups import create_generic_security_groups
from iam import create_iam
from jenkins import create_jenkins
from keypair import create_keypair
from s3 import create_s3_cft_and_artifacts_buckets, CFT_PUBLIC_BUCKET, create_flow_logs_dog_food_bucket,\
    create_mongodb_backups_bucket, create_region_external_s3_artifact_buckets
from utils import PRIVATE_SUBNET_TYPE_NAME, PUBLIC_SUBNET_TYPE_NAME, VPC_TYPE_NAME
from vpc_network import create_lightlytics_vpc_and_network, create_vpc_and_subnets_per_external_regions
from certificate import create_acm_for_stack
from security import set_lightlytics_security_polices
from eks import create_eks_cluster
from eks import create_eks_cluster
from msk import create_msk
from vpc_peering import create_vpc_peering


keypair = create_keypair()
network = create_lightlytics_vpc_and_network()
vpc = network.get(VPC_TYPE_NAME)
private_subnets = network.get(PRIVATE_SUBNET_TYPE_NAME)
public_subnets = network.get(PUBLIC_SUBNET_TYPE_NAME)
if pulumi.get_stack() == "prod":
    ecr = create_ecr()
s3_buckets = create_s3_cft_and_artifacts_buckets()
s3_flow_logs_dog_food_bucket = create_flow_logs_dog_food_bucket()
s3_mongodb_backups_bucket = create_mongodb_backups_bucket()
iam_polices = create_iam(s3_buckets.get(CFT_PUBLIC_BUCKET), s3_mongodb_backups_bucket)
eks_cluster, open_id_connect = create_eks_cluster(vpc, public_subnets, private_subnets, keypair, iam_polices)
bastion = create_bastion(vpc, public_subnets, keypair)
msk = create_msk(private_subnets, vpc, eks_cluster)
security_groups = create_generic_security_groups(vpc, bastion.outputs['BastionSecurityGroupID'])
private_key = create_access_token()
jenkins = create_jenkins(vpc, private_subnets, public_subnets, security_groups, keypair)
cert = create_acm_for_stack()
external_s3_buckets = create_region_external_s3_artifact_buckets()
security = set_lightlytics_security_polices()
external_networks = create_vpc_and_subnets_per_external_regions()
vpcs_peering = create_vpc_peering(network, external_networks)
