import argparse
import base64
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime

import boto3
import docker

DOCKER_FILE_EXTENSION = '*.Dockerfile'
os.environ['DOCKER_BUILDKIT'] = '1'
MAIN_BRANCHES = ["master", "main"]


def _build_docker_image(ms, branch_name, build_number, skip_test, test_only):
    old_path = os.getcwd()
    os.chdir('lightlytics/{}'.format(ms))
    docker_file = glob.glob(DOCKER_FILE_EXTENSION)
    if len(docker_file) == 0:
        print(
            "Error - cannot find docker file in this ms :{} directory".
                format(ms)
        )
        sys.exit(1)
    elif len(docker_file) > 1:
        print(
            "Error - found more than 1 docker file in this ms:{} directory".
                format(ms)
        )
        sys.exit(1)
    ms_name = docker_file[0].split('.')[0]
    image_tag = f"{ms_name}:{branch_name}.{build_number}"
    if skip_test is True:
        skip_test_arg = "0"
    else:
        skip_test_arg = "1"
    response = subprocess.run(
        [
            "/usr/bin/docker", "build", "--network=host", "-f", docker_file[0],
            "-t", image_tag, "--build-arg",
            f"BUILD_NUMBER_ARG={build_number}", "--build-arg",
            f"BUILD_BRANCH_ARG={branch_name}", "--build-arg",
            f"SKIP_TESTS={skip_test_arg}", "--build-arg",
            f"BUILD_DATE_ARG={get_timestamp}", "."
        ]
    )
    if response.returncode != 0:
        print("Failed to build {} image - exit".format(ms))
        sys.exit(1)
    tag_as_latest(image_tag)
    os.chdir(old_path)
    if test_only:
        get_report_file(image_tag)


def _handler_reports_dir():
    directories = ["reports", "coverage"]
    for dir_name in directories:
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        os.mkdir(dir_name)


def get_report_file(image_name):
    ms_name = image_name.split(":")[0]
    container_name = "test-{}".format(image_name).replace(':', '-')
    docker_client.containers.run(image_name, detach=True, name=container_name)
    report_file_path = "{}:{}".format(container_name, "/reports/result.xml")
    coverage_file_path = "{}:{}".format(
        container_name, "/coverage/coverage.xml"
    )
    subprocess.run(
        [
            "/usr/bin/docker", "cp", report_file_path,
            "reports/result_{}.xml".format(ms_name)
        ]
    )
    subprocess.run(
        [
            "/usr/bin/docker", "cp", coverage_file_path,
            "coverage/coverage_{}.txt".format(ms_name)
        ]
    )
    docker_client.containers.get(container_name).remove(force=True, v=True)


def build_docker_images(
        microservices, branch_name, build_number, skip_test=False, test_only=False
):
    for ms in microservices:
        if os.path.isdir('lightlytics/{}'.format(ms)):
            print("Build {} microservice".format(ms))
            _build_docker_image(
                ms, branch_name, build_number, skip_test, test_only
            )
        else:
            print("Error - cannot find ms:{}".format(ms))
            sys.exit(1)


def upload_to_ecr(
        microservices, branch_name, build_number, skip_test=False, test_only=False
):
    print("Uploading images to ECR")
    get_ecr_password()
    old_path = os.getcwd()
    for ms in microservices:
        os.chdir(f'lightlytics/{ms}')
        docker_file = glob.glob('%s' % DOCKER_FILE_EXTENSION)
        if len(docker_file) == 0:
            print(
                "Error - cannot find docker file in this ms :{} directory".
                    format(ms)
            )
            sys.exit(1)
        elif len(docker_file) > 1:
            print(
                "Error - found more than 1 docker file in this ms:{} directory".
                    format(ms)
            )
            sys.exit(1)
        ms_name = docker_file[0].split('.')[0]
        image_tag = f"{ms_name}:{branch_name}.{build_number}"
        upload_image_to_ecr(image_tag, branch_name)
        os.chdir(old_path)


def tag_as_latest(image_name):
    image = docker_client.images.get(image_name)
    base_image_name = image_name.split(":")[0]
    latest_tag = f'{base_image_name}:latest'
    image.tag(latest_tag)


def tag_as_latest_for_ecr(image_name):
    image = docker_client.images.get(image_name)
    base_image_name = image_name.split(":")[0]
    latest_tag = f'{ecr_url}/{base_image_name}:latest'
    image.tag(latest_tag)
    print(f"tagging image as latest: {latest_tag}")
    return latest_tag


def tag_image_for_ecr(image_tag):
    image = docker_client.images.get(image_tag)
    ecr_tag = f'{ecr_url}/{image_tag}'
    image.tag(ecr_tag)
    return ecr_tag


def build_shared_image(branch, build_number):
    print("Build shared image")
    old_path = os.getcwd()
    os.chdir('lightlytics/shared')
    image_tag = f"shared:{branch}.{build_number}"
    response = subprocess.run(
        [
            "/usr/bin/docker", "build", "--no-cache", "--network=host", "-f",
            "shared.Dockerfile", "-t", image_tag, "."
        ]
    )
    if response.returncode != 0:
        print("Failed to build shared image - exit")
        sys.exit(1)
    tag_as_latest(image_tag)
    os.chdir(old_path)


def get_timestamp():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def upload_image_to_ecr(image_tag, branch_name):
    print(f"Upload image {image_tag} to ecr")
    repository_name = image_tag.split(":")[0]
    create_ecr_repository(repository_name)
    login_output = docker_client.login(
        username="AWS",
        password=ecr_password,
        registry=f"{ecr_url}/{repository_name}"
    )
    ecr_image_name = tag_image_for_ecr(image_tag)
    docker_client.images.push(ecr_image_name)

    if branch_name in MAIN_BRANCHES:
        ecr_image_name = tag_as_latest_for_ecr(image_tag)
        print(f"pushing {ecr_image_name}")
        docker_client.images.push(ecr_image_name)


def get_ecr_password():
    global ecr_password, ecr_url
    ecr_credentials = ecr_client.get_authorization_token(
    )['authorizationData'][0]
    ecr_password = (
        base64.b64decode(ecr_credentials['authorizationToken']
                         ).replace(b'AWS:', b'').decode('utf-8')
    )
    ecr_url = ecr_credentials['proxyEndpoint'].replace('https://', '')


def check_repository_exists(repository_name):
    print("Check if repository {} exists".format(repository_name))
    repositories = ecr_client.describe_repositories()['repositories']
    for repository in repositories:
        if repository_name == repository['repositoryName']:
            print("Repository {} already exists".format(repository_name))
            return True
    return False


def create_ecr_repository(repository_name):
    if not check_repository_exists(repository_name):
        print("Create new repository: {}".format(repository_name))
        ecr_client.create_repository(repositoryName=repository_name)


if __name__ == "__main__":
    global docker_client, ecr_client
    docker_client = docker.from_env()
    ecr_client = boto3.client('ecr')
    parser = argparse.ArgumentParser(description='Build lightlytics script')
    parser.add_argument(
        "--branch_name", help="The git branch name", required=True
    )
    parser.add_argument(
        "--build_number", help="Jenkins build number", required=True
    )
    parser.add_argument("--skip_test", dest='skip_test', action='store_true')
    parser.add_argument("--test_only", dest='test_only', action='store_true')
    parser.add_argument("--microservices", nargs='+', required=True)
    parser.set_defaults(skip_test=False)
    args = parser.parse_args()

    if args.test_only:
        _handler_reports_dir()

    build_shared_image(args.branch_name, args.build_number)
    build_docker_images(
        args.microservices, args.branch_name, args.build_number, args.skip_test,
        args.test_only
    )
    if not args.test_only:
        upload_to_ecr(
            args.microservices, args.branch_name, args.build_number,
            args.skip_test, args.test_only
        )
