"""An AWS Python Pulumi program"""

# todo: protect resources against deletion?
# todo: secrets - https://www.pulumi.com/docs/intro/concepts/programming-model/#secrets
# todo: Jenkins
import pulumi
conf = pulumi.Config()
from access_token import create_access_token
from bastion import create_bastion, get_bastion
from eks import create_eks_cluster, get_eks_cluster
from generic_secuity_groups import create_generic_security_groups
from keypair import create_keypair, get_keypair
from mongodb import create_mongodb_cft_cluster
from msk import create_msk, get_msk
from neo4j import create_neo4j
from vpc_peering import create_vpc_peering
from utils import PRIVATE_SUBNET_TYPE_NAME, PUBLIC_SUBNET_TYPE_NAME, VPC_TYPE_NAME
from vpc_network import create_lightlytics_vpc_and_network, create_vpc_and_subnets_per_external_regions,\
    get_lightlytics_vpc_and_network

from lightlytics_users import create_lightlytics_support_user_credentials
from waf import create_waf


if conf.require_bool("fullDeploymnet"):
    keypair = create_keypair()
    network = create_lightlytics_vpc_and_network()
    vpc = network.get(VPC_TYPE_NAME)
    private_subnets = network.get(PRIVATE_SUBNET_TYPE_NAME)
    public_subnets = network.get(PUBLIC_SUBNET_TYPE_NAME)
    lightlytics_support_user = create_lightlytics_support_user_credentials()
    bastion = create_bastion(vpc, public_subnets, keypair)
    eks_cluster, open_id_connect = create_eks_cluster(vpc, public_subnets, private_subnets, keypair)
    mongodb = create_mongodb_cft_cluster(vpc, private_subnets, bastion, keypair, eks_cluster)
    msk = create_msk(private_subnets, vpc, eks_cluster)
    security_groups = create_generic_security_groups(vpc, bastion.outputs['BastionSecurityGroupID'])
    neo4j = create_neo4j(vpc, private_subnets, keypair, bastion, eks_cluster)
    private_key = create_access_token()
    external_networks = create_vpc_and_subnets_per_external_regions()
    vpcs_peering = create_vpc_peering(network, external_networks)
    waf = create_waf()
else:
    keypair = get_keypair()
    network = get_lightlytics_vpc_and_network()
    vpc = network.get(VPC_TYPE_NAME)
    private_subnets = network.get(PRIVATE_SUBNET_TYPE_NAME)
    lightlytics_support_user = create_lightlytics_support_user_credentials()
    eks_cluster = get_eks_cluster()
    bastion = get_bastion()
    msk = get_msk()
    mongodb = create_mongodb_cft_cluster(vpc, private_subnets, bastion, keypair, eks_cluster)
    neo4j = create_neo4j(vpc, private_subnets, keypair, bastion, eks_cluster)
    private_key = create_access_token()
    waf = create_waf()

