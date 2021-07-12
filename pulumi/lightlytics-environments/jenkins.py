import pulumi
import pulumi_aws as aws
from pulumi import export
from pulumi_aws import route53, ec2

from certificate import create_acm_certificate
from generic_secuity_groups import HTTP_FROM_ALL, ALLOW_ALL_TRAFFIC_FROM_BASTION, ALLOW_ALL_EGRESS_TRAFFIC
from utils import get_resource_name_by_convention, get_lightlytics_com_route53_zone, \
    get_route53_record_name_by_convention

conf = pulumi.Config()
JENKINS_SLAVES_COUNT = 1


def _create_jenkins_slaves_sg(vpc, security_groups, master_sg):
    # this is an empty group to allow slaves receive traffic from master
    name, tag = get_resource_name_by_convention("sg_access_from_jenkins_master")
    return [
        ec2.SecurityGroup(
            name,
            vpc_id=vpc.id,
            name=name,
            tags=tag,
            egress=[
                ec2.SecurityGroupEgressArgs(
                    description="Jenkins Slave Egress Rule",
                    from_port=0,
                    to_port=0,
                    protocol=-1,
                    cidr_blocks=["0.0.0.0/0"]
                )
            ],
            ingress=[
                ec2.SecurityGroupIngressArgs(
                    description="Allow All traffic from Jenkins Master",
                    from_port=0,
                    to_port=0,
                    protocol=-1,
                    security_groups=[master_sg]
                )
            ]

        ),
        security_groups[ALLOW_ALL_TRAFFIC_FROM_BASTION],
        security_groups[ALLOW_ALL_EGRESS_TRAFFIC],
    ]


def _create_jenkins_mater_sg(vpc):
    # this is an empty group to allow slaves receive traffic from master
    name, tag = get_resource_name_by_convention("sg_jenkins_master")
    return ec2.SecurityGroup(
        name,
        vpc_id=vpc.id,
        name=name,
        tags=tag
    )


def create_jenkins(vpc, private_subnets, public_subnets, security_groups, keypair):
    jenkins_dns_name = conf.require("JenkinsDns")
    jenkins_master_sg = _create_jenkins_mater_sg(vpc)
    jenkins_master = _create_jenkins_instance(private_subnets[0], jenkins_master_sg, security_groups, keypair)
    ssl_cert_validation = _create_jenkins_acm(jenkins_dns_name)
    lb = _create_jenkins_lb(public_subnets, jenkins_master, ssl_cert_validation, security_groups)
    _create_jenkins_elb_route53_alias_record(lb, jenkins_dns_name)
    _create_jenkins_internal_dns_for_ssh(jenkins_master)
    jenkins_slaves_sg = _create_jenkins_slaves_sg(vpc, security_groups, jenkins_master_sg)
    create_jenkins_slaves(JENKINS_SLAVES_COUNT, private_subnets, jenkins_slaves_sg, keypair)


def _create_jenkins_instance(subnet, jenkins_master_sg, security_groups, keypair):
    # jenkins_sgs = create_jenkins_security_group(vpc, security_groups)
    name, tag = get_resource_name_by_convention("jenkins")
    jenkins_volume = _get_jenkins_root_device_args(200)
    jenkins_instance = aws.ec2.Instance(name,
                                        ami='ami-0885b1f6bd170450c',
                                        instance_type=ec2.InstanceType.M5_LARGE,
                                        tags=tag,
                                        subnet_id=subnet,
                                        key_name=keypair.key_name,
                                        associate_public_ip_address=False,
                                        disable_api_termination=False,
                                        volume_tags=tag,
                                        root_block_device=jenkins_volume,
                                        vpc_security_group_ids=[security_groups[HTTP_FROM_ALL],
                                                                security_groups[ALLOW_ALL_TRAFFIC_FROM_BASTION],
                                                                security_groups[ALLOW_ALL_EGRESS_TRAFFIC],
                                                                jenkins_master_sg],
                                        )
    export("jenkins_public_ip", jenkins_instance.public_ip)
    return jenkins_instance


def create_jenkins_slaves(count, subnets, jenkins_slaves_sg, keypair):
    jenkins_slaves = []
    jenkins_slave_volume = _get_jenkins_root_device_args(250)
    for i in range(0, count):
        name, tag = get_resource_name_by_convention("jenkins-slave", i)
        jenkins_slave_instance = aws.ec2.Instance(name,
                                                  ami='ami-0885b1f6bd170450c',
                                                  instance_type=ec2.InstanceType.M5_LARGE,
                                                  tags=tag,
                                                  subnet_id=subnets[i % len(subnets)],
                                                  key_name=keypair.key_name,
                                                  associate_public_ip_address=False,
                                                  disable_api_termination=False,
                                                  volume_tags=tag,
                                                  root_block_device=jenkins_slave_volume,
                                                  vpc_security_group_ids=jenkins_slaves_sg,
                                                  )
        _create_jenkins_slave_internal_route53_records(i, jenkins_slave_instance.private_ip)
        pulumi.export(name, jenkins_slave_instance.private_ip)
        jenkins_slaves.append(jenkins_slave_instance)
    return jenkins_slaves


def _get_jenkins_root_device_args(volume_size):
    return ec2.InstanceRootBlockDeviceArgs(
        delete_on_termination=False,
        volume_size=volume_size
    )


def _create_jenkins_slave_internal_route53_records(index, private_ip):
    zone = get_lightlytics_com_route53_zone()
    resource_name, _ = get_route53_record_name_by_convention("jenkins-slave", route53.RecordType.A, index)
    record = route53.Record(
        resource_name,
        zone_id=zone.zone_id,
        type=route53.RecordType.A,
        name=f"jenkins-slave-{index + 1}",
        records=[private_ip],
        ttl=300
    )


def _create_jenkins_elb_route53_alias_record(jenkins_lb, jenkins_dns_name):
    # the url is not just jenkins.lightlytics.com, safer this way
    zone = get_lightlytics_com_route53_zone()
    resource_name, _ = get_route53_record_name_by_convention("jenkins-lb-alias-record", route53.RecordType.A)
    record = route53.Record(
        resource_name,
        zone_id=zone.zone_id,
        type=route53.RecordType.A,
        name=jenkins_dns_name,
        aliases=[aws.route53.RecordAliasArgs(
            name=jenkins_lb.dns_name,
            zone_id=jenkins_lb.zone_id,
            evaluate_target_health=True,
        )]
    )
    return record


def _create_jenkins_internal_dns_for_ssh(jenkins_instance):
    # the url is not just jenkins.lightlytics.com, safer this way
    zone = get_lightlytics_com_route53_zone()
    jenkins_internal_dns_name = conf.require("JenkinsInternalDns")
    resource_name, _ = get_route53_record_name_by_convention("jenkins-internal-record", route53.RecordType.A)
    record = route53.Record(
        resource_name,
        zone_id=zone.zone_id,
        type=route53.RecordType.A,
        name=jenkins_internal_dns_name,
        records=[jenkins_instance.private_ip],
        ttl=300
    )
    export('jenkins_internal_dns', jenkins_internal_dns_name)
    return record


# https://www.pulumi.com/docs/reference/pkg/aws/acm/certificatevalidation/
def _create_jenkins_acm(jenkins_dns_name):
    name = "jenkins-cert"
    return create_acm_certificate(jenkins_dns_name, name)


def _create_jenkins_lb(public_subnets, jenkins_instance, cert_validation, security_groups):
    name, tag = get_resource_name_by_convention("jenkins")
    return aws.elb.LoadBalancer(name,
                                subnets=[subnet.id for subnet in public_subnets],
                                listeners=[
                                    aws.elb.LoadBalancerListenerArgs(
                                        instance_port=8080,
                                        instance_protocol="http",
                                        lb_port=443,
                                        lb_protocol="https",
                                        ssl_certificate_id=cert_validation.certificate_arn
                                    )
                                ],
                                health_check=aws.elb.LoadBalancerHealthCheckArgs(
                                    healthy_threshold=2,
                                    unhealthy_threshold=2,
                                    timeout=3,
                                    target="HTTP:8080/login",
                                    interval=30,
                                ),
                                instances=[jenkins_instance],
                                cross_zone_load_balancing=True,
                                idle_timeout=400,
                                connection_draining=True,
                                connection_draining_timeout=400,
                                security_groups=[security_groups[HTTP_FROM_ALL],
                                                 security_groups[ALLOW_ALL_EGRESS_TRAFFIC]],
                                tags=tag)
