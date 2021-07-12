import pulumi
from pulumi_aws import ecr


def create_ecr():
    ms_list = [
        "account", "alert", "analyzer", "collection", "customers", "front-end", "front-gate", "scan",
        "configurationfiles", "snapshot", "terraform", "topology", "changes", "tasks"
    ]

    for ms in ms_list:
        repository = ecr.Repository(ms, name=ms, tags={'Name': ms})
        pulumi.export(f"{ms}-ecr", repository.repository_url)
