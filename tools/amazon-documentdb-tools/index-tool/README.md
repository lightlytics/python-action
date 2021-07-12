# Amazon DocumentDB Index Tool

The Index Tool makes it easier to migrate only indexes (not data) between a source MongoDB deployment and a Amazon
DocumentDB cluster. The Index Tool can also help you find potential compatibility issues between your source databases
and Amazon DocumentDB. You can use the Index Tool to dump indexes and database metadata, or you can use the tool against
an existing dump created with the mongodump tool.

Features:

- Dump just the indexes from a running mongodb instance/replica set
- Outputs in the same dump format that mongodump uses
- Checks indexes, collections, and databases for compatibility with Amazon DocumentDB
- Checks indexes for unsupported index types
- Checks collections for unsupported options
- Restores supported indexes (without data) to Amazon DocumentDB

## Installing

Clone the repository, then run the following command in the repo top-level director:
`pip install -r requirements.txt`

