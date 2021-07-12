import argparse
import base64
import boto3
import docker

DEV_AWS_ACCOUNT_ID = "219342927623"
PROD_AWS_ACCOUNT_ID = "624907860825"
docker_client = docker.from_env()


def upload_image_to_ecr(ecr_prod_data, repository, image_name):
    print("Upload image {} to ecr".format(image_name))
    ecr_url = ecr_prod_data.get("ecr_url")
    ecr_password = ecr_prod_data.get("ecr_password")
    docker_client.login(
        username="AWS",
        password=ecr_password,
        registry="{}/{}".format(ecr_url, repository)
    )
    docker_client.images.push(image_name)


def tag_image_for_prod_ecr(image_name):
    image = docker_client.images.get(image_name)
    image_tag_prod = image_name.replace(DEV_AWS_ACCOUNT_ID, PROD_AWS_ACCOUNT_ID)
    image.tag(image_tag_prod)
    return image_tag_prod


def get_ecr_password(ecr_client):
    ecr_credentials = ecr_client.get_authorization_token(
    )['authorizationData'][0]
    ecr_password = (
        base64.b64decode(ecr_credentials['authorizationToken']
                        ).replace(b'AWS:', b'').decode('utf-8')
    )
    ecr_url = ecr_credentials['proxyEndpoint'].replace('https://', '')
    return {'ecr_password': ecr_password, 'ecr_url': ecr_url}


def pull_and_push_images(dev_ecr_client, prod_ecr_client, image_name):
    ecr_dev_data = get_ecr_password(dev_ecr_client)
    ecr_prod_data = get_ecr_password(prod_ecr_client)
    ecr_url = ecr_dev_data.get("ecr_url")
    ecr_password = ecr_dev_data.get("ecr_password")
    for repository in get_repositories(dev_ecr_client):
        image_to_pull = "{}/{}:{}".format(ecr_url, repository, image_name)
        print(image_to_pull)
        docker_client.login(
            username="AWS",
            password=ecr_password,
            registry="{}/{}".format(ecr_url, repository)
        )
        docker_client.images.pull(image_to_pull)
        image_to_push = tag_image_for_prod_ecr(image_to_pull)
        upload_image_to_ecr(ecr_prod_data, repository, image_to_push)


def get_repositories(ecr_client):
    print("get repository list")
    repository_list = []
    exclude_list = ['graphdb', 'lightlytics/neo4j']
    repositories = ecr_client.describe_repositories()['repositories']
    for repository in repositories:
        repository_name = repository.get('repositoryName')
        if repository_name not in exclude_list:
            repository_list.append(repository_name)
    return repository_list


if __name__ == "__main__":
    dev_session = boto3.session.Session(profile_name='default')
    ecr_client_dev = dev_session.client('ecr')

    prod_session = boto3.session.Session(profile_name="lightlytics-production")
    ecr_client_prod = prod_session.client('ecr')

    parser = argparse.ArgumentParser(
        description='Copy lightlytics build from dev to prod'
    )
    parser.add_argument(
        "--image_name", help="The image name(branch:version)", required=True
    )
    args = parser.parse_args()

    pull_and_push_images(ecr_client_dev, ecr_client_prod, args.image_name)
