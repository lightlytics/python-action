import pulumi
from pulumi_aws import cloudformation, route53

from utils import get_resource_name_by_convention, get_route53_record_name_by_convention, \
    get_lightlytics_com_route53_zone


def create_bastion(vpc, public_subnets, keypair):
    name, tag = get_resource_name_by_convention("bastion")
    bastion = cloudformation.Stack(
        name,
        tags=tag,
        template_url="https://aws-quickstart.s3.amazonaws.com/quickstart-linux-bastion/templates/linux-bastion.template",
        parameters={
            "VPCID": vpc.id,
            "PublicSubnet1ID": public_subnets[0].id,
            "PublicSubnet2ID": public_subnets[1].id,
            "RemoteAccessCIDR": "0.0.0.0/0",
            "KeyPairName": keypair.key_name
        },
        capabilities=['CAPABILITY_IAM']
    )
    _create_bastion_route53_record(bastion.outputs)
    pulumi.export("bastion", bastion.outputs)
    pulumi.export("bastion-sg", bastion.outputs['BastionSecurityGroupID'])

    return bastion


def _create_bastion_route53_record(bastion_stack_outputs):
    record_name = "bastion.lightlytics.com"
    record_type = route53.RecordType.A
    zone = get_lightlytics_com_route53_zone()
    resource_name, _ = get_route53_record_name_by_convention(record_name, record_type)
    route53.Record(
        resource_name,
        zone_id=zone.zone_id,
        name=record_name,
        type=record_type,
        ttl=300,
        records=[bastion_stack_outputs['EIP1']]
    )
