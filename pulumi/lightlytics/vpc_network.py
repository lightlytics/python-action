import pulumi
from pulumi_aws import ec2, get_availability_zones, Provider

from utils import get_resource_name_by_convention, get_subnet_name_by_convention, get_private_networks, \
    get_public_networks, PRIVATE_SUBNET_TYPE_NAME, PUBLIC_SUBNET_TYPE_NAME, PRIVATE_ROUTE_TABLES_TYPE_NAME,\
    VPC_TYPE_NAME

conf = pulumi.Config()


def create_vpc_and_subnets_per_external_regions():
    external_networks = {}
    regions = conf.require_object('externalRegions')
    for region in regions:
        provider = Provider(f'external-network-{region}-provider', region=region, profile="prod")
        vpc = _create_vpc(provider, region)
        all_zones = get_availability_zones(
            state="available",
            opts=pulumi.ResourceOptions(provider=provider)
        )
        zone_names = all_zones.names[:2]
        private_subnets = _create_private_subnets_for_zones(vpc, zone_names, provider, region)
        public_subnets = _create_public_subnets_for_zones(vpc, zone_names, provider, region)
        nat_gateways = _create_nat_gateways_on_external_networks(public_subnets, provider, region)
        internet_gateway = _create_internet_gateway_on_external_network(vpc, provider, region)
        private_route_tables = _create_private_route_tables_and_associations_on_external_network(
            vpc, nat_gateways, private_subnets, provider, region)
        _create_public_route_table_and_association_on_external_network(vpc, internet_gateway, public_subnets,
                                                                       provider, region)
        external_networks[region] = {
            VPC_TYPE_NAME: vpc,
            PRIVATE_SUBNET_TYPE_NAME: private_subnets,
            PUBLIC_SUBNET_TYPE_NAME: public_subnets,
            PRIVATE_ROUTE_TABLES_TYPE_NAME: private_route_tables

        }
    return external_networks


def create_lightlytics_vpc_and_network():
    region = conf.require('primaryRegion')
    provider = Provider(region.replace('-', ''), region=region, profile="prod")
    vpc = _create_vpc(provider, region)
    all_zones = get_availability_zones(state="available")
    # We use only 3 azs atm
    zone_names = all_zones.names[:3]
    private_subnets = _create_private_subnets_for_zones(vpc, zone_names)
    public_subnets = _create_public_subnets_for_zones(vpc, zone_names)
    nat_gateways = _create_nat_gateways(public_subnets)
    internet_gateway = _create_internet_gateway(vpc)
    private_route_tables = _create_private_route_tables_and_associations(vpc, nat_gateways, private_subnets)
    _create_public_route_table_and_association(vpc, internet_gateway, public_subnets)

    return {
        VPC_TYPE_NAME: vpc,
        PRIVATE_SUBNET_TYPE_NAME: private_subnets,
        PUBLIC_SUBNET_TYPE_NAME: public_subnets,
        PRIVATE_ROUTE_TABLES_TYPE_NAME: private_route_tables
    }


def _create_vpc(provider, region_name):
    name, name_tag = get_resource_name_by_convention(f'vpc-{region_name}')
    vpc = ec2.Vpc(
        name,
        cidr_block=conf.require(f'VpcBlock-{region_name}'),
        tags=name_tag,
        instance_tenancy='default',
        enable_dns_support=True,
        enable_dns_hostnames=True,
        opts=pulumi.ResourceOptions(provider=provider)
    )
    pulumi.export(f'vpc-id-{region_name}', vpc.id)
    return vpc


# SUBNETS
def _create_private_subnets_for_zones(vpc, zone_names, provider=None, region_name=None):
    private_subnets_networks = get_private_networks()
    if provider is not None:
        return _create_subnets_for_zones_on_external_network(PRIVATE_SUBNET_TYPE_NAME, private_subnets_networks, vpc,
                                                             zone_names, provider, region_name)
    else:
        return _create_subnets_for_zones(PRIVATE_SUBNET_TYPE_NAME, private_subnets_networks, vpc, zone_names)


def _create_public_subnets_for_zones(vpc, zone_names, provider=None, region_name=None):
    public_subnets_networks = get_public_networks()
    if provider is not None:
        return _create_subnets_for_zones_on_external_network(PUBLIC_SUBNET_TYPE_NAME, public_subnets_networks,
                                                             vpc, zone_names, provider, region_name)
    else:
        return _create_subnets_for_zones(PUBLIC_SUBNET_TYPE_NAME, public_subnets_networks, vpc, zone_names)


def _create_subnets_for_zones(subnet_type, subnet_networks, vpc, zone_names):
    subnets = []
    for i, zone_name in enumerate(zone_names):
        name, tags = get_subnet_name_by_convention(subnet_type, i, vpc, zone_name)
        network_number = subnet_networks[i]
        subnet = ec2.Subnet(
            name,
            vpc_id=vpc.id,
            cidr_block=f'10.0.{network_number}.0/24',
            tags=tags,
            availability_zone=zone_name,
            map_public_ip_on_launch=subnet_type == PUBLIC_SUBNET_TYPE_NAME,

        )
        subnets.append(subnet)
    return subnets


def _create_subnets_for_zones_on_external_network(subnet_type, subnet_networks, vpc, zone_names, provider, region_name):
    subnets = []
    cidr_block = conf.require(f'VpcBlock-{region_name}').split('/')[0].split('.')
    for i, zone_name in enumerate(zone_names):
        name, tags = get_subnet_name_by_convention(subnet_type, i, vpc, zone_name)
        network_number = subnet_networks[i]
        cidr_block[2] = str(network_number)
        subnet = ec2.Subnet(
            name,
            vpc_id=vpc.id,
            cidr_block='.'.join(cidr_block) + "/24",
            tags=tags,
            availability_zone=zone_name,
            map_public_ip_on_launch=subnet_type == PUBLIC_SUBNET_TYPE_NAME,
            opts=pulumi.ResourceOptions(provider=provider)
        )
        subnets.append(subnet)
    return subnets


def _create_nat_gateways(public_subnets):
    nat_gateways = []
    for i, subnet in enumerate(public_subnets):
        elastic_ip = _create_elastic_ip(i)
        name, name_tag = get_resource_name_by_convention('nat_gateway', i)
        nat_gateway = ec2.NatGateway(name, allocation_id=elastic_ip, subnet_id=subnet.id, tags=name_tag)
        nat_gateways.append(nat_gateway)

    return nat_gateways


def _create_nat_gateways_on_external_networks(public_subnets, provider, region_name):
    nat_gateways = []
    for i, subnet in enumerate(public_subnets):
        elastic_ip = _create_elastic_ip_on_external_networks(i, provider, region_name)
        name, name_tag = get_resource_name_by_convention(f'nat_gateway-{region_name}', i)
        nat_gateway = ec2.NatGateway(
            name,
            allocation_id=elastic_ip,
            subnet_id=subnet.id,
            tags=name_tag,
            opts=pulumi.ResourceOptions(provider=provider)
        )
        nat_gateways.append(nat_gateway)

    return nat_gateways


def _create_elastic_ip_on_external_networks(suffix, provider, region_name):
    name, name_tag = get_resource_name_by_convention(f'elastic_ip-{region_name}', suffix)
    return ec2.Eip(
        name,
        tags=name_tag,
        opts=pulumi.ResourceOptions(provider=provider)
    )


def _create_elastic_ip(suffix):
    name, name_tag = get_resource_name_by_convention("elastic_ip", suffix)
    return ec2.Eip(name, tags=name_tag)


def _create_private_route_tables_and_associations(vpc, nat_gateways, private_subnets):
    private_route_tables = []
    for i, nat_gateway in enumerate(nat_gateways):
        name, name_tag = get_resource_name_by_convention('private_route_table', i)
        private_route_table = ec2.RouteTable(
            name,
            tags=name_tag,
            vpc_id=vpc.id,
            routes=[
                ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0", nat_gateway_id=nat_gateway.id
                )
            ]
        )
        name, name_tag = get_resource_name_by_convention('route_table_association_private', i)
        ec2.RouteTableAssociation(
            name,
            subnet_id=private_subnets[i],
            route_table_id=private_route_table
        )
        private_route_tables.append(private_route_table)
    return private_route_tables


def _create_private_route_tables_and_associations_on_external_network(vpc, nat_gateways, private_subnets,
                                                                      provider, region_name):
    private_route_tables = []
    for i, nat_gateway in enumerate(nat_gateways):
        name, name_tag = get_resource_name_by_convention(f'private_route_table-{region_name}', i)
        private_route_table = ec2.RouteTable(
            name,
            tags=name_tag,
            vpc_id=vpc.id,
            routes=[
                ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0", nat_gateway_id=nat_gateway.id
                )
            ],
            opts=pulumi.ResourceOptions(provider=provider)
        )
        name, name_tag = get_resource_name_by_convention(f'route_table_association_private-{region_name}', i)
        ec2.RouteTableAssociation(
            name,
            subnet_id=private_subnets[i],
            route_table_id=private_route_table,
            opts=pulumi.ResourceOptions(provider=provider)
        )
        private_route_tables.append(private_route_table)
    return private_route_tables


# IGW + PUBLIC ROUTE TABLES
def _create_internet_gateway(vpc):
    name, name_tag = get_resource_name_by_convention('igw')
    return ec2.InternetGateway(
        name, tags=name_tag, vpc_id=vpc.id
    )


def _create_internet_gateway_on_external_network(vpc, provider, region_name):
    name, name_tag = get_resource_name_by_convention(f'igw-{region_name}')
    return ec2.InternetGateway(
        name,
        tags=name_tag,
        vpc_id=vpc.id,
        opts=pulumi.ResourceOptions(provider=provider)
    )


def _create_public_route_table_and_association(vpc, igw, public_subnets):
    name, name_tag = get_resource_name_by_convention('public_route_table')
    public_route_table = ec2.RouteTable(
        name,
        vpc_id=vpc.id,
        routes=[
            ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id)
        ],
        tags=name_tag
    )
    for i, public_subnet in enumerate(public_subnets):
        name, name_tag = get_resource_name_by_convention('route_table_association_public', i)
        ec2.RouteTableAssociation(
            name,
            subnet_id=public_subnet.id,
            route_table_id=public_route_table.id,
        )


def _create_public_route_table_and_association_on_external_network(vpc, igw, public_subnets, provider, region_name):
    name, name_tag = get_resource_name_by_convention(f'public_route_table-{region_name}')
    public_route_table = ec2.RouteTable(
        name,
        vpc_id=vpc.id,
        routes=[
            ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id)
        ],
        tags=name_tag,
        opts=pulumi.ResourceOptions(provider=provider)
    )
    for i, public_subnet in enumerate(public_subnets):
        name, name_tag = get_resource_name_by_convention(f'route_table_association_public-{region_name}', i)
        ec2.RouteTableAssociation(
            name,
            subnet_id=public_subnet.id,
            route_table_id=public_route_table.id,
            opts=pulumi.ResourceOptions(provider=provider)
        )