import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


def create_aws_alb_ingress_controller_chart():
    aws_alb_ingress_controller = Chart(
        "aws-alb-ingress-controller",
        ChartOpts(
            chart="aws-alb-ingress-controller",
            fetch_opts=FetchOpts(
                repo="https://charts.helm.sh/incubator"
            ),
            values={
                "awsRegion": "us-east-1",
                "awsVpcID": "vpc-02e6ba06e29a3bdb2",
                "clusterName": "LightlyticsProd",
                "rbac": {
                    "create": "true",
                    "serviceAccount": {
                        "create": "true",
                        "annotations": {
                            "eks.amazonaws.com/role-arn": "arn:aws:iam::624907860825:role/alb_ingress_controller_iam_role"
                        }
                    }
                }
            }
        )
    )
    pulumi.export("aws_alb_ingress_controller", aws_alb_ingress_controller.id)