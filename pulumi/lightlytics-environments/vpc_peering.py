import pulumi
import pulumi_aws as aws
from utils import get_resource_name_by_convention, PRIVATE_ROUTE_TABLES_TYPE_NAME

conf = pulumi.Config()


def create_vpc_peering(primary_region_network, external_networks):
    vpcs_peering = []
    for key, value in external_networks.items():
        name, name_tag = get_resource_name_by_convention(f'vpc-peering-{key}')
        vpc_peering = aws.ec2.VpcPeeringConnection(
            name,
            tags=name_tag,
            vpc_id=primary_region_network.get('vpc').id,
            peer_vpc_id=value.get('vpc').id,
            auto_accept=False,
            peer_region=key,
        )
        vpcs_peering.append(vpc_peering)
        provider = aws.Provider(f'vpc-peering-{key}', region=key, profile="prod")
        name, name_tag = get_resource_name_by_convention(f'vpc-peering-accepter{key}')
        aws.ec2.VpcPeeringConnectionAccepter(
            name,
            tags=name_tag,
            auto_accept=True,
            vpc_peering_connection_id=vpc_peering.id,
            opts=pulumi.ResourceOptions(provider=provider)
        )
        _edit_external_private_route_table(key, provider, value.get(PRIVATE_ROUTE_TABLES_TYPE_NAME), vpc_peering)
        _edit_primary_private_route_tables(primary_region_network.get(PRIVATE_ROUTE_TABLES_TYPE_NAME), vpc_peering, key)
    return vpcs_peering


def _edit_external_private_route_table(region_name, provider, route_tables, vpc_peering):
    us_east_1_cidr_block = conf.require(f'VpcBlock-us-east-1')
    for i, route_table in enumerate(route_tables):
        name, _ = get_resource_name_by_convention(f'vpc-peering-route-{region_name}', i)
        aws.ec2.Route(
            name,
            route_table_id=route_table.id,
            destination_cidr_block=us_east_1_cidr_block,
            vpc_peering_connection_id=vpc_peering.id,
            opts=pulumi.ResourceOptions(provider=provider)
        )


def _edit_primary_private_route_tables(route_tables, vpc_peering, region_name):
    external_region_cidr_block = conf.require(f'VpcBlock-{region_name}')
    for i, route_table in enumerate(route_tables):
        name, _ = get_resource_name_by_convention(f'vpc-peering-route-primary-{region_name}', i)
        aws.ec2.Route(
            name,
            route_table_id=route_table.id,
            destination_cidr_block=external_region_cidr_block,
            vpc_peering_connection_id=vpc_peering.id,
        )

