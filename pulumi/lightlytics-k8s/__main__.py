"""A Kubernetes Python Pulumi program"""

import pulumi
from prod_aws_alb_ingress_controller import create_aws_alb_ingress_controller_chart
from prod_aws_external_secrets import create_aws_external_secret_chart
from prod_logzio import create_logzio_chart

aws_alb_ingress_controller_chart = create_aws_alb_ingress_controller_chart()
aws_external_secrets_chart = create_aws_external_secret_chart()
logzio_chart = create_logzio_chart()



