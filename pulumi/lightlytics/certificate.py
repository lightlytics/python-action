import pulumi
import pulumi_aws as aws

from utils import get_resource_name_by_convention, get_lightlytics_com_route53_zone, \
    get_route53_record_name_by_convention

conf = pulumi.Config()


# https://www.pulumi.com/docs/reference/pkg/aws/acm/certificatevalidation/
def create_acm_for_stack():
    name = "lightlytics-cert"
    stack_main_dns_name = conf.require("domainWildCard")
    return create_acm_certificate(stack_main_dns_name, name)


def create_acm_certificate(dns_name, name_raw):
    name, tag = get_resource_name_by_convention(name_raw)
    cert = aws.acm.Certificate(name,
                               domain_name=dns_name,
                               tags=tag,
                               validation_method="DNS")
    # NOTE: https://github.com/pulumi/pulumi/issues/5028
    records = cert.domain_validation_options.apply(lambda opts: create_route53_acm_validation_records(opts))
    name, _ = get_resource_name_by_convention(f"{name_raw}-validation")
    fqdns = records.apply(lambda validation_record: [record.fqdn for record in validation_record])
    return aws.acm.CertificateValidation(name,
                                         certificate_arn=cert.arn,
                                         validation_record_fqdns=fqdns)


def create_route53_acm_validation_records(validation_options):
    zone = get_lightlytics_com_route53_zone()
    records = []
    for i, dvo in enumerate(validation_options):
        resource_name, tag = get_route53_record_name_by_convention(dvo.resource_record_name,
                                                                   dvo.resource_record_type,
                                                                   i)
        record = aws.route53.Record(resource_name,
                                    name=dvo.resource_record_name,
                                    allow_overwrite=True,
                                    records=[dvo.resource_record_value],
                                    ttl=60,
                                    type=dvo.resource_record_type,
                                    zone_id=zone.zone_id)
        records.append(record)
    return records
