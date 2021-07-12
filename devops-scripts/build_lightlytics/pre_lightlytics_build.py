import argparse
import docker
import os
import pymongo
import random
import secrets
import socket
import string
import sys
import tarfile
import time
from bson.json_util import loads
from jinja2 import Environment, FileSystemLoader


def _load_template(folder_name, template_file):
    env = Environment(loader=FileSystemLoader(folder_name))
    template = env.get_template(template_file)
    return template


def genrate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(20))


def render_template(template, **kwargs):
    print(kwargs)
    return template.render(**kwargs)


def write_config_test_file(render_template):
    with open("lightlytics/shared/config-test.ini", "w") as fh:
        fh.write(render_template)


def genrate_port():
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port_number = random.randint(1024, 65535)
        results = sock.connect_ex(('127.0.0.1', port_number))
        if results == 0:
            print("Port is open genrate anthoer one")
            time.sleep(1)
        else:
            sock.close()
            return port_number


def _check_container_exists(container_name):
    if client.containers.list(filters={'name': container_name}):
        print(
            "container with the same name: {} already running - exit".
            format(container_name)
        )
        sys.exit(1)
    else:
        return True


def _restart_container(container_name):
    container = client.containers.get(container_name)
    container.restart()


def _run_command_on_container(
    container_name,
    command_list,
    user="root",
    privileged=True,
    workdir="/var/lib/neo4j"
):
    container = client.containers.get(container_name)
    print(command_list)
    print(container.exec_run(command_list, tty=True, stdin=True))


def create_mongo_container(branch_name, build_number):
    mongo_password = genrate_password()
    mongo_user = "admin"
    container_name = "mongo-{}-{}".format(branch_name, build_number)
    _check_container_exists(container_name)
    mongo_port = genrate_port()
    client.containers.run(
        "mongo:latest",
        detach=True,
        name=container_name,
        ports={'27017/tcp': mongo_port},
        environment={
            'MONGO_INITDB_DATABASE': 'Lightlytics',
            'MONGO_INITDB_ROOT_USERNAME': mongo_user,
            'MONGO_INITDB_ROOT_PASSWORD': mongo_password
        }
    )
    import_mongo_collections(mongo_user, mongo_password, mongo_port)

    return {
        'mongo_address': '127.0.0.1',
        'mongo_port': str(mongo_port),
        'mongo_user': mongo_user,
        'mongo_password': mongo_password
    }


def create_neo4j_container(branch_name, build_number):
    neo4j_password = genrate_password()
    neo4j_user = "neo4j"
    container_name = "neo4j-{}-{}".format(branch_name, build_number)
    _check_container_exists(container_name)
    neo4j_http_port = genrate_port()
    neo4j_bolt_port = genrate_port()
    client.containers.run(
        "neo4j:latest",
        detach=True,
        name=container_name,
        ports={
            '7474/tcp': neo4j_http_port,
            '7687/tcp': neo4j_bolt_port
        },
        environment={'NEO4J_AUTH': '{}/{}'.format(neo4j_user, neo4j_password)}
    )
    apoc_jar_name = "apoc-4.1.0.0-all.jar"
    apoc_jar = os.path.join(payload_dir, apoc_jar_name)
    copy_to(
        apoc_jar,
        "{}:/var/lib/neo4j/plugins/{}".format(container_name, apoc_jar_name)
    )

    gds_jar_name = "neo4j-graph-data-science-1.4.0-alpha05-standalone.jar"
    gds_jar = os.path.join(payload_dir, gds_jar_name)
    copy_to(
        gds_jar,
        "{}:/var/lib/neo4j/plugins/{}".format(container_name, gds_jar_name)
    )

    _run_command_on_container(
        container_name,
        "/bin/bash -c \"echo \'dbms.security.procedures.unrestricted=gds.*,apoc.*\' >> conf/neo4j.conf\"",
        user="neo4j"
    )
    _run_command_on_container(
        container_name,
        "/bin/bash -c \"echo \'dbms.security.procedures.whitelist=apoc.*,gds.*\' >> conf/neo4j.conf\"",
        user="neo4j"
    )

    _restart_container(container_name)
    return {
        'neo4j_address': '127.0.0.1',
        'neo4j_port': neo4j_bolt_port,
        'neo4j_user': neo4j_user,
        'neo4j_password': neo4j_password
    }


def import_mongo_collections(mongo_user, mongo_password, mongo_port):
    uri = "mongodb://{}:{}@127.0.0.1:{}".format(
        mongo_user, mongo_password, mongo_port
    )
    client = pymongo.MongoClient(uri)
    database = client['lightlytics']

    collection = database['keys']
    keys_file = os.path.join(payload_dir, 'keys.json')
    with open(keys_file) as f:
        file_data = f.read()
    file_data = loads(file_data)
    collection.insert_many(file_data)

    collection = database['users']
    users_file = os.path.join(payload_dir, 'users.json')
    with open(users_file) as f:
        file_data = f.read()
    file_data = loads(file_data)
    collection.insert_many(file_data)


def copy_to(src, dst):
    name, dst = dst.split(':')
    container = client.containers.get(name)
    current_dir = os.getcwd()
    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()
    data = open(src + '.tar', 'rb').read()
    print(dst)
    container.put_archive(os.path.dirname(dst), data)
    os.chdir(current_dir)


if __name__ == "__main__":
    global base_dir, payload_dir, client
    base_dir = os.path.dirname(os.path.realpath(__file__))
    payload_dir = os.path.join(base_dir, 'payload')
    client = docker.from_env()
    template_dict = {}
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--branch_name", help="The git branch name")
    parser.add_argument("--build_number", help="Jenkins build number")
    args = parser.parse_args()

    template_dict.update(
        create_mongo_container(args.branch_name, args.build_number)
    )
    template_dict.update(
        create_neo4j_container(args.branch_name, args.build_number)
    )
    print(template_dict)
    config_test_template = _load_template(
        'lightlytics/shared', 'config-test.ini.template'
    )
    write_config_test_file(
        render_template(config_test_template, **template_dict)
    )
