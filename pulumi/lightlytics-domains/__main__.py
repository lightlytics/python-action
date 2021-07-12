"""An AWS Python Pulumi program"""
from route53 import create_lightlytics_com_route53_zone_and_records
from ses import create_lightlytics_com_domain_ses

route53 = create_lightlytics_com_route53_zone_and_records()
ses = create_lightlytics_com_domain_ses(route53["zone"])
