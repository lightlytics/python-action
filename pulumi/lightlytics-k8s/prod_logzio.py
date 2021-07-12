import pulumi
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts


def create_logzio_chart():
    logzio = Chart(
        "logzio-filebeat",
        ChartOpts(
            chart="logzio-k8s-logs",
            namespace="kube-system",
            fetch_opts=FetchOpts(
                repo="https://logzio.github.io/logzio-helm/filebeat"
            ),
            values={
                "configType": "autodiscover",
                "secrets": {
                    "logzioShippingToken": "qOlTYEiRAyCVLwJRcyDLJbsypsTvUCpS",
                    "clusterName": "LightlyticsProd"
                }
            }
        )
    )
    pulumi.export("logzio", logzio.id)
