# Pulumi Route53 Setup

1. This should not be touched, only to update.
2. The fact that you create the domain and hosted zone doesn't mean that you own the domain, you must move the domain
   from the previous account (case you are moving this)

```shell
# List zone records:
aws route53 list-resource-record-sets --hosted-zone-id <ZONE_ID>

```