import argparse
import docker
import os


def _check_container_exists(container_name):
    if client.containers.list(filters={'name': container_name}):
        return True
    else:
        print("container with the name: {} not exists".format(container_name))
        return False


def check_file_exists(file_path):
    return os.path.isfile(file_path)


def remove_mongo_container(client, branch_name, build_number):
    container_name = "mongo-{}-{}".format(branch_name, build_number)
    if _check_container_exists(container_name):
        client.containers.get(container_name).remove(force=True, v=True)


def remove_neo4j_container(client, branch_name, build_number):
    container_name = "neo4j-{}-{}".format(branch_name, build_number)
    if _check_container_exists(container_name):
        client.containers.get(container_name).remove(force=True, v=True)


def remove_config_test_file():
    if check_file_exists("lightlytics/shared/config-test.ini"):
        os.remove("lightlytics/shared/config-test.ini")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--branch_name", help="The git branch name")
    parser.add_argument("--build_number", help="Jenkins build number")
    args = parser.parse_args()

    client = docker.from_env()
    remove_mongo_container(client, args.branch_name, args.build_number)
    remove_neo4j_container(client, args.branch_name, args.build_number)
