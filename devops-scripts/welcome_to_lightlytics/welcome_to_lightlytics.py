import argparse
import docker
import os
import pymongo
import tarfile
from bson.json_util import loads


def create_mongo_container(client, mongo_password):
    client.containers.run(
        "mongo:latest",
        detach=True,
        name="mongo-dev2",
        ports={'27017/tcp': 47017},
        environment={
            'MONGO_INITDB_DATABASE': 'Lightlytics',
            'MONGO_INITDB_ROOT_USERNAME': 'admin',
            'MONGO_INITDB_ROOT_PASSWORD': mongo_password
        }
    )


def create_neo4j_container(neo4j_password):
    client.containers.run(
        "neo4j:latest",
        detach=True,
        name="neo4j-dev",
        ports={
            '7474/tcp': 7474,
            '7687/tcp': 7687
        },
        environment={'NEO4J_AUTH': 'neo4j/{}'.format(neo4j_password)}
    )


def _install_gds():
    pass


def import_mongo_collections(mongo_password):
    uri = 'mongodb://admin:' + mongo_password + '@127.0.0.1:47017'
    client = pymongo.MongoClient(uri)
    database = client['lightlytics']

    collection = database['keys']
    with open('keys.json') as f:
        file_data = f.read()
    file_data = loads(file_data)
    collection.insert_many(file_data)

    collection = database['users']
    with open('users.json') as f:
        file_data = f.read()
    file_data = loads(file_data)
    collection.insert_one(file_data)


def copy_to(src, dst):
    name, dst = dst.split(':')
    container = client.containers.get(name)
    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()
    data = open(src + '.tar', 'rb').read()
    container.put_archive(os.path.dirname(dst), data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Welcome to Lightlytics script'
    )
    parser.add_argument("--mongo_password", help="The mongo db admin password")
    parser.add_argument("--neo4j_password", help="The neo4j user password")
    args = parser.parse_args()

    client = docker.from_env()
    create_mongo_container(client, args.mongo_password)
    import_mongo_collections(args.mongo_password)
    create_neo4j_container(args.neo4j_password)
