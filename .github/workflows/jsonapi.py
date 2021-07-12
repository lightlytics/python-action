import json
import typer
import os
import requests


def json_for_api(path_plan, path_metadata):
    input_Path_plan = os.environ["INPUT_Path_plan"]
    input_Path_metadata = os.environ["INPUT_Path_metadata"]
    plan_terraform = json.load(open(path_plan))
    metadata_git = json.load(open(path_metadata))

    remove_aws_credentials(plan_terraform)

    JsonFile = {'plan': plan_terraform,
                'metadata': metadata_git}

    send_request_to_lightlytics(JsonFile)

    print(f"::set-output name=Path_plan::{path_plan}")
    print(f"::set-output name=Path_metadata::{path_metadata}")

def remove_aws_credentials(tf_file):
    tf_file["configuration"]["provider_config"]["aws"]["expressions"].pop("access_key")
    tf_file["configuration"]["provider_config"]["aws"]["expressions"].pop("secret_key")

def send_request_to_lightlytics(json_file):
    url = "https://staging.lightops.io/api/v1/collection/terraform"
    headers = {'Content-type': 'application/json', 'X-Lightlytics-Token': '4EtCBoOncQ6CHPNkd00eH8oTY8y8FqTRr7zR7A5J2yE'}
    r = requests.post(url, data=json.dumps(json_file), headers=headers)
    print(r)


def main(path_metadata, path_plan):
    json_for_api(path_plan, path_metadata)
# (path_plan: str = "./terraform/ofri.json", path_metadata: str = "./terraform/ofri2.json")

if __name__ == "__main__":
    # typer.run(main)
    main()