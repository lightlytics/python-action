import pulumi
from pulumi_aws import ses, route53

from utils import get_route53_record_name_by_convention


def create_lightlytics_com_domain_ses(lightlytics_com_zone):
    # Setup Email Identity
    email_identity = ses.EmailIdentity(
        "lightlytics_email_identity", email="donotreply@lightlytics.com"
    )
    pulumi.export("ses_email_identity", email_identity.email)

    # Setup Domain Identity
    domain_identity = ses.DomainIdentity('lightlytics_domain_identity', domain="lightlytics.com")
    # Setup Domain Verification
    record_type = "TXT"
    resource_name, _ = get_route53_record_name_by_convention("lightlytics_domain_verification_record", record_type)
    ses_verification_record = route53.Record(resource_name,
                                             name="_amazonses.lightlytics.com",
                                             records=[domain_identity.verification_token],
                                             ttl=600,
                                             type=record_type,
                                             zone_id=lightlytics_com_zone.zone_id)
    pulumi.export("ses_verification_record", ses_verification_record.name)

    # Setup Domain DKIM
    domain_dkim = ses.DomainDkim('lightlytics_domain_dkim', domain=domain_identity.domain)
    ses_dkim_records = []
    # DO NOT TRY to enumerate dkim_tokens it causes an endless loop
    for i in range(3):
        record_type = "CNAME"
        resource_name, _ = get_route53_record_name_by_convention("domainkey.lightlytics.com", record_type, i)
        dkim_record = route53.Record(resource_name,
                                     name=domain_dkim.dkim_tokens[i].apply(
                                         lambda token: f"{token}._domainkey.lightlytics.com"),
                                     records=[
                                         domain_dkim.dkim_tokens[i].apply(lambda token: f"{token}.dkim.amazonses.com")],
                                     ttl=600,
                                     type=record_type,
                                     zone_id=lightlytics_com_zone.zone_id)
        ses_dkim_records.append(dkim_record)
        pulumi.export(f"ses_dkim_record-{i}", dkim_record.name)

    # Setup Configuration Set
    configuration_set = ses.ConfigurationSet(
        'lightlytics_configuration_set', name="lightlytics_configuration_set"
    )
    cloudwatch_events = ses.EventDestination(
        "lightlytics_ses_cloudwatch_events",
        configuration_set_name=configuration_set.name,
        enabled=True,
        matching_types=["bounce", "send", "delivery", "reject"],
        cloudwatch_destinations=[
            # value_soruce = The source for the value. It can be either `"messageTag"` or `"emailHeader"`
            ses.EventDestinationCloudwatchDestinationArgs(
                default_value="Production",
                dimension_name="environment",
                value_source="emailHeader"
            ),
            ses.EventDestinationCloudwatchDestinationArgs(
                default_value="Production",
                dimension_name="release",
                value_source="messageTag"
            )
        ]
    )
    pulumi.export("ses_configuration_set", configuration_set.name)
    pulumi.export("ses_cloudwatch_events", cloudwatch_events.id)
    return {
        "email_identity": email_identity,
        "dkim_records": ses_dkim_records,
        "domain_identity": domain_identity,
        "configuration_set": configuration_set
    }
