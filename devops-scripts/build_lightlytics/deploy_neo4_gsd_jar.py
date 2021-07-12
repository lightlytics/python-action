import argparse


def copy_jar_file_to_relevant_dirs():
    pass


def git_commit():
    pass


def run_ansible_playbook():
    pass


def build_docker_image():
    pass


def upload_to_ecr():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy the jar to the staging neo4j server(with ansible) and update "
                                                 "the neo4j lightlytics docker image")
    parser.add_argument("--file",
                        required=True,
                        type=str,
                        help="The file location")
    args = parser.parse_args()

    print(args.file)
