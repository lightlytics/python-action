import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


def create_aws_external_secret_chart():
    aws_external_secret = Chart(
        "kubernetes-external-secrets",
        ChartOpts(
            chart="kubernetes-external-secrets",
            fetch_opts=FetchOpts(
                repo="https://external-secrets.github.io/kubernetes-external-secrets"
            ),
            values={
                "env": {
                    "AWS_REGION": "us-east-1",
                    "AWS_DEFAULT_REGION": "us-east-1",
                },
                "securityContext": {
                    "fsGroup": "65534"
                },
                "serviceAccount": {
                    "create": "true",
                    "annotations": {
                        "eks.amazonaws.com/role-arn": "arn:aws:iam::624907860825:role/secret_manager_iam_role"
                    }
                }
            }
        )
    )
    pulumi.export("aws_external_secret", aws_external_secret.id)
