import argparse
import boto3
import sys
import json
import time

ec2_boto_client = boto3.client("ec2")
elbv2_boto_client = boto3.client("elbv2")
route53_boto_client = boto3.client("route53")


def get_boto_client_by_region(method, region):
    return boto3.client(method, region_name=region)


def get_primary_loadbalancer_ip_address(release):
    loadbalancer_private_ip_addresses_list = []
    primary_region_network_loadbalancer_dns = get_network_loadbalancer(release).get('DNSName')
    primary_region_network_loadbalancer_dns_prefix = primary_region_network_loadbalancer_dns.split('.')[0] \
        .replace('-', '/')
    loadbalancer_description_string = f'ELB net/{primary_region_network_loadbalancer_dns_prefix}'
    network_interfaces = ec2_boto_client.describe_network_interfaces(
        Filters=[
            {
                'Name': 'description',
                'Values': [
                    loadbalancer_description_string
                ]
            }
        ]
    ).get('NetworkInterfaces')
    for network_interface in network_interfaces:
        loadbalancer_private_ip_addresses_list.append(network_interface.get('PrivateIpAddress'))
    if loadbalancer_private_ip_addresses_list:
        return loadbalancer_private_ip_addresses_list
    print('Cannot find active ip address for release:{} network load balancer'.format(release))


def get_region_vpc_information(region, release):
    vpc_peering_json_file = f'devops-scripts/build_lightlytics/prod/payload/{release}_vpc_peering_mapping.json'
    with open(vpc_peering_json_file) as json_file:
        vpc_peering_dict = json.load(json_file)
    for vpc_region_info in vpc_peering_dict.get('regions'):
        if vpc_region_info.get('region_name') == region:
            return vpc_region_info.get('data')
    print("cannot find vpc peering information for this region:{}".format(region))


def create_region_target_group(region, release, vpc_id, ip_addresses):
    print("Create region target group")
    region_elbv2_boto_client = boto3.client("elbv2", region_name=region)
    target_group = region_elbv2_boto_client.create_target_group(
        Name=f'{release}-{region}-pvl-tg',
        TargetType="ip",
        Protocol='TCP',
        Port=443,
        VpcId=vpc_id
    ).get('TargetGroups')[0]
    for ip in ip_addresses:
        region_elbv2_boto_client.register_targets(
            TargetGroupArn=target_group.get('TargetGroupArn'),
            Targets=[
                {
                    'Id': ip,
                    'AvailabilityZone': 'all'
                }
            ]
        )
    return target_group.get('TargetGroupArn')


def create_region_network_loadbalancer(region, release):
    print("Create region:{} network loadbalancer".format(region))
    ip_addresses = get_primary_loadbalancer_ip_address(release)
    region_elbv2_boto_client = boto3.client("elbv2", region_name=region)
    vpc_peering_info = get_region_vpc_information(region, release)
    target_group_arn = create_region_target_group(region, release, vpc_peering_info.get('vpc_id'), ip_addresses)
    region_loadbalancer = region_elbv2_boto_client.create_load_balancer(
        Name=f'{release}-{region}-pvl-nlb',
        Type="network",
        Scheme='internal',
        Subnets=vpc_peering_info.get('private_subnets')
    ).get('LoadBalancers')[0]
    region_elbv2_boto_client.create_listener(
        LoadBalancerArn=region_loadbalancer.get('LoadBalancerArn'),
        Protocol='TCP',
        Port=80,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group_arn
            }
        ]
    )
    region_elbv2_boto_client.create_listener(
        LoadBalancerArn=region_loadbalancer.get('LoadBalancerArn'),
        Protocol='TCP',
        Port=443,
        DefaultActions=[
            {
                'Type': 'forward',
                'TargetGroupArn': target_group_arn
            }
        ]
    )
    return region_loadbalancer.get('LoadBalancerArn')


def get_network_loadbalancer(release):
    print("Search the network loadbalnce arn")
    value_tag = f'{release}/collection-producer'
    key_tag = 'kubernetes.io/service-name'
    loadbalancer_list = elbv2_boto_client.describe_load_balancers().get('LoadBalancers')
    for loadbalancer in loadbalancer_list:
        if loadbalancer.get("Type") == "network":
            loadbalancer_tags = elbv2_boto_client.describe_tags(
                ResourceArns=[loadbalancer.get("LoadBalancerArn")]
            ).get("TagDescriptions")[0].get('Tags')
            for loadbalancer_tag in loadbalancer_tags:
                if loadbalancer_tag.get('Key') == key_tag and loadbalancer_tag.get('Value') == value_tag:
                    return loadbalancer
    print("Cannot find release:{} network loadbalancer, exit".format(release))
    sys.exit(1)


def wait_until_nlb_is_ready(loadbalancer_arn, region):
    print("Check if nlb is in active state")
    tries = 10
    elbv2_region_boto_client = get_boto_client_by_region("elbv2", region)
    for lb_try in range(tries):
        loadbalancer = elbv2_region_boto_client.describe_load_balancers(
            LoadBalancerArns=[
                loadbalancer_arn
            ]
        ).get('LoadBalancers')[0]
        loadbalancer_status = loadbalancer.get('State').get('Code')
        if loadbalancer_status == "active":
            return True
        time.sleep(60)
    print("loadbalancer: {} not in active status,  exit".format(loadbalancer_arn))
    sys.exit(1)


def create_endpoint_service(release, environment, region, loadbalancer_arn):
    if check_endpoint_exists(loadbalancer_arn, region):
        print("Endpoint service already exists - exit")
        sys.exit(1)
    domain_name = get_domain_name(environment)
    print("Create endpoint service")
    wait_until_nlb_is_ready(loadbalancer_arn, region)
    ec2_region_boto_client = get_boto_client_by_region("ec2", region)
    vpc_endpoint_service = ec2_region_boto_client.create_vpc_endpoint_service_configuration(
        NetworkLoadBalancerArns=[loadbalancer_arn],
        AcceptanceRequired=True,
        PrivateDnsName=f'{release}-{region}-pvl.{domain_name}',
        TagSpecifications=[
            {
                "ResourceType": "vpc-endpoint-service",
                "Tags": [
                    {
                        'Key': 'Name',
                        'Value': f'{release}-{region}-pvl'
                    }

                ]
            }
        ]
    )
    vpc_endpoint_service_id = vpc_endpoint_service.get('ServiceConfiguration').get('ServiceId')
    print("Modify vpc endpoint service permissions")
    ec2_region_boto_client.modify_vpc_endpoint_service_permissions(
        ServiceId=vpc_endpoint_service_id,
        AddAllowedPrincipals=[
            '*'
        ]
    )
    verification_name = vpc_endpoint_service.get('ServiceConfiguration').get('PrivateDnsNameConfiguration').get('Name')
    verification_value = vpc_endpoint_service.get('ServiceConfiguration').get('PrivateDnsNameConfiguration').get(
        'Value')
    create_dns_record(domain_name, verification_name, verification_value)


def create_dns_record(domain_name, verification_name, verification_value):
    print("Create dns record")
    hosted_zone = get_hosted_zone(domain_name)
    print(hosted_zone)
    if hosted_zone is not None:
        route53_boto_client.change_resource_record_sets(
            HostedZoneId=hosted_zone,
            ChangeBatch={
                'Comment': f'add-{verification_name}->{verification_value}',
                'Changes': [
                    {
                        'Action': 'CREATE',
                        'ResourceRecordSet': {
                            'Name': f'{verification_name}.{domain_name}',
                            'Type': 'TXT',
                            'TTL': 1600,
                            'ResourceRecords': [
                                {
                                    'Value': f'\"{verification_value}\"'
                                }
                            ]
                        }
                    }
                ]
            }
        )


def get_hosted_zone(domain):
    print("Get hosed zone")
    hosted_zone_list = route53_boto_client.list_hosted_zones().get('HostedZones')
    for hosted_zone in hosted_zone_list:
        if hosted_zone.get('Name') == f'{domain}.':
            return hosted_zone.get('Id').split('/')[-1]
    return None


def check_endpoint_exists(loadbalancer_arn, region):
    ec2_region_boto_client = get_boto_client_by_region("ec2", region)
    endpoint_services = ec2_region_boto_client.describe_vpc_endpoint_service_configurations().get('ServiceConfigurations')
    for endpoint_service in endpoint_services:
        if loadbalancer_arn in endpoint_service.get('NetworkLoadBalancerArns'):
            return True
    return False


def get_domain_name(environment):
    if environment == "production":
        return "lightlytics.com"
    else:
        return "lightops.io"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create endpoint service(private link) for the requested release")
    parser.add_argument("--release",
                        required=True,
                        type=str,
                        help="The helm release name")
    parser.add_argument("--environment",
                        required=True,
                        type=str,
                        help="The environment name e.g - staging"
                        )
    parser.add_argument("--regions",
                        required=True,
                        help="The AWS region name")
    args = parser.parse_args()

    regions = args.regions.split(',')

    for req_region in regions:
        if req_region != "us-east-1":
            region_loadbalancer_arn = create_region_network_loadbalancer(req_region, args.release)
            create_endpoint_service(
                args.release,
                args.environment,
                req_region,
                region_loadbalancer_arn
            )
        else:
            create_endpoint_service(args.release, args.environment, req_region,
                                    get_network_loadbalancer(args.release).get("LoadBalancerArn"))
