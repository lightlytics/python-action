# Ansible

## Install

```shell
brew install ansible
```

## Basic Usage:

Check reachability:

```shell
ansible <host> -a "command"
ansible <host> -m ping
```

Running a playbook example:

```shell
ansible-playbook playbooks/neo4j-plugin-installation.yaml
```
