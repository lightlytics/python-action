import pulumi
import pulumi_aws as aws
from utils import get_resource_name_by_convention


def create_waf():
    name, name_tag = get_resource_name_by_convention("waf")
    aws_waf = aws.wafv2.WebAcl(name,
                               default_action=aws.wafv2.WebAclDefaultActionArgs(
                                   allow=aws.wafv2.WebAclDefaultActionAllowArgs(),
                               ),
                               description="AWS WAF associated with environment ALB",
                               rules=[aws.wafv2.WebAclRuleArgs(
                                   name="aws-waf-common-rules",
                                   override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                                       count=aws.wafv2.WebAclRuleOverrideActionCountArgs(),
                                   ),
                                   priority=1,
                                   statement=aws.wafv2.WebAclRuleStatementArgs(
                                       managed_rule_group_statement=aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                                           excluded_rules=[
                                               {
                                                   "name": "SizeRestrictions_QUERYSTRING",
                                               },
                                               {
                                                   "name": "NoUserAgent_HEADER",
                                               },
                                           ],
                                           name="AWSManagedRulesCommonRuleSet",
                                           vendor_name="AWS",
                                       ),
                                   ),
                                   visibility_config={
                                       "cloudwatchMetricsEnabled": True,
                                       "metric_name": "friendly-rule-metric-name",
                                       "sampledRequestsEnabled": True,
                                   },
                               )],
                               scope="REGIONAL",
                               visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
                                   cloudwatch_metrics_enabled=True,
                                   metric_name="friendly-metric-name",
                                   sampled_requests_enabled=True,
                               ),
                               opts=pulumi.ResourceOptions(ignore_changes=["rules"]),)
    pulumi.export('aws_awf', aws_waf.arn)
