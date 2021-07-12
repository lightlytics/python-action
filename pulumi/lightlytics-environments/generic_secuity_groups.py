# List of security groups that we can use in different situations
from pulumi_aws import ec2

from utils import get_resource_name_by_convention

SSH_FROM_ALL = 'ssh_from_all'
HTTP_FROM_ALL = 'http_from_all'
ALLOW_ALL_TRAFFIC_FROM_BASTION = 'all_from_bastion'
ALLOW_ALL_EGRESS_TRAFFIC = 'allow_all_egress'


def create_generic_security_groups(vpc, bastion_sg):
    security_groups = {}
    ssh_sg = _create_ssh_from_all_ips_sg(vpc)
    http_sg = _http_and_https_from_all_ips_sg(vpc)
    all_traffic_egress_sg = _allow_outbound_traffic_to_all_ips(vpc)
    all_from_bastion_sg = _all_from_bastion(vpc, bastion_sg)
    security_groups[HTTP_FROM_ALL] = http_sg
    security_groups[ALLOW_ALL_EGRESS_TRAFFIC] = all_traffic_egress_sg
    security_groups[ALLOW_ALL_TRAFFIC_FROM_BASTION] = all_from_bastion_sg
    security_groups[SSH_FROM_ALL] = ssh_sg

    return security_groups


def _create_ssh_from_all_ips_sg(vpc):
    name, tag = get_resource_name_by_convention("sg_ssh_from_all_ips")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag,
        ingress=[
            ec2.SecurityGroupIngressArgs(
                description="SSH All Ips",
                from_port=22,
                to_port=22,
                protocol="TCP",
                cidr_blocks=["0.0.0.0/0"]
            ),
        ])


def _http_and_https_from_all_ips_sg(vpc):
    name, tag = get_resource_name_by_convention("sg_http_from_all_ips")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag,
        ingress=[
            ec2.SecurityGroupIngressArgs(
                description="HTTP All Ips",
                from_port=80,
                to_port=80,
                protocol="TCP",
                cidr_blocks=["0.0.0.0/0"]
            ),
            ec2.SecurityGroupIngressArgs(
                description="HTTP 8080 All Ips",
                from_port=8080,
                to_port=8080,
                protocol="TCP",
                cidr_blocks=["0.0.0.0/0"]
            ),
            ec2.SecurityGroupIngressArgs(
                description="HTTPS All Ips",
                from_port=443,
                to_port=443,
                protocol="TCP",
                cidr_blocks=["0.0.0.0/0"]
            ),
        ])


def _allow_outbound_traffic_to_all_ips(vpc):
    name, tag = get_resource_name_by_convention("sg_outbound_traffic_to_all_ips")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag,
        egress=[
            ec2.SecurityGroupIngressArgs(
                description="Allow all egress traffic from instance",
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["0.0.0.0/0"]
            )
        ])


def _all_from_bastion(vpc, bastion_sg):
    name, tag = get_resource_name_by_convention("sg_ssh_from_bastion")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag,
        ingress=[
            ec2.SecurityGroupIngressArgs(
                description="Access from bastion server",
                from_port=0,
                to_port=0,
                protocol="-1",
                security_groups=[bastion_sg]
            ),
        ])
