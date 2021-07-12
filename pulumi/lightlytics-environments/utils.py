import random
import socket
import string

import certifi
import pulumi
# By default Config() is using the configuration for the current project (aka current dir with Pulumi.yaml)
# More info: https://www.pulumi.com/docs/intro/concepts/programming-model/#reading-configuration-values
from OpenSSL import SSL
from pulumi_aws import route53, ec2

conf = pulumi.Config()

PUBLIC_SUBNET_TYPE_NAME = "public_subnet"
PRIVATE_SUBNET_TYPE_NAME = "private_subnet"
PRIVATE_ROUTE_TABLES_TYPE_NAME = "private_route_tables"
VPC_TYPE_NAME = "vpc"

def get_resource_name_by_convention(name, suffix=None):
    stack_name = pulumi.get_stack()
    resource_name = f"{stack_name}-{name}"
    if suffix is not None:
        suffix += 1
        # since all arrays are starting at 0 we must always add one to make it count form 1
        resource_name = f"{resource_name}_{suffix}"
    resource_name_tag = {
        'Name': resource_name,
        'Customer': stack_name
    }
    return resource_name, resource_name_tag


# example: prod-lightlytics-public_subnet_1-us-east-1a
def get_subnet_name_by_convention(subnet_type, suffix, zone_name):
    partial_name, _ = get_resource_name_by_convention(subnet_type, suffix)
    name = f'{partial_name}-{zone_name}'
    if subnet_type == PUBLIC_SUBNET_TYPE_NAME:
        tags = _eks_public_subnet_tags(name)
    if subnet_type == PRIVATE_SUBNET_TYPE_NAME:
        tags = _eks_private_subnet_tags(name)
    return name, tags


# https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html#vpc-tagging
def _eks_private_subnet_tags(name_tag):
    stack_name = pulumi.get_stack()
    return {
        'Name': name_tag,
        'kubernetes.io/role/internal-elb': "1",
        f'kubernetes.io/cluster/{stack_name}-eks_cluster': "shared"
    }


def _eks_public_subnet_tags(name_tag):
    stack_name = pulumi.get_stack()
    return {
        'Name': name_tag,
        'kubernetes.io/role/elb': "1",
        f'kubernetes.io/cluster/{stack_name}-eks_cluster': "shared"
    }


def get_public_networks():
    start = conf.require_int('PublicSubnetNetworkStart')
    end = start + conf.require_int('PublicSubnetNetworkCount')
    return list(range(start, end))


def get_private_networks():
    total_network_count = conf.require_int('PrivateSubnetNetworkStart') + conf.require_int('PrivateSubnetNetworkCount')
    return list(range(total_network_count))


def create_eks_oidc_thumbprint():
    hostname = "oidc.eks.us-east-1.amazonaws.com"
    port = 443

    context = SSL.Context(method=SSL.TLSv1_METHOD)
    context.load_verify_locations(cafile=certifi.where())

    conn = SSL.Connection(context, socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    conn.settimeout(5)
    conn.connect((hostname, port))
    conn.setblocking(1)
    conn.do_handshake()
    conn.set_tlsext_host_name(hostname.encode())

    thumbprint = conn.get_peer_cert_chain()[-1].digest("sha1")
    conn.close()
    return thumbprint.decode("utf-8").replace(":", "").lower()


def get_key_value_from_list(dict_list, **kw):
    return filter(lambda i: all((i[k] == v for (k, v) in kw.items())), dict_list)


def get_random_password(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join((random.choice(letters_and_digits) for i in range(length)))


def get_route53_record_name_by_convention(record_name, record_type, suffix=None):
    resource_name = f"{record_name}-{record_type}"
    if suffix is not None:
        suffix += 1
        # since all arrays are starting at 0 we must always add one to make it count form 1
        resource_name = f"{resource_name}_{suffix}"
    resource_name_tag = {'Name': resource_name}
    return resource_name, resource_name_tag


def get_lightlytics_com_route53_zone():
    zone = route53.get_zone(name="lightlytics.com.", private_zone=False)
    return zone


def create_volume_attachment(name, instance, volume, device_name="/dev/sda2"):
    name, _ = get_resource_name_by_convention(name)
    return ec2.VolumeAttachment(name,
                                device_name=device_name,
                                volume_id=volume.id,
                                instance_id=instance.id)
