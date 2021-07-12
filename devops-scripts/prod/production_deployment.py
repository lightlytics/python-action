import argparse
import json
import subprocess
import os
import stat
from pathlib import Path
import sys
import glob
from jinja2 import Environment, FileSystemLoader
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


def _git_stuff():
    pass


def _get_latest_neo4j_gds_plugin():
    list_of_files = glob.glob('playbooks/payloads/neo4j/plugins/*.jar')
    latest_file = max(list_of_files, key=os.path.getctime)
    logging.info(f'found latest jar file:{latest_file.split("/")[-1]}')
    return '/'.join(latest_file.split('/')[1:])


def run_neo4j_ansible_playbook(environment):
    logging.info("Start running neo4j playbook")
    old_pwd = os.getcwd()
    os.chdir('ansible')
    neo4j_ansible_command = subprocess.run(["ansible-playbook",
                                            "playbooks/neo4j-plugin-installation.yaml",
                                            "-i",
                                            f"inventory/{environment}",
                                            "--extra-vars",
                                            f"gds_jar_file_location={_get_latest_neo4j_gds_plugin()}"
                                            ]
                                           )
    logging.info(neo4j_ansible_command)
    os.chdir(old_pwd)


def run_bastion_ansible_playbooks(environment):
    logging.info("Start running bastion playbooks")
    old_pwd = os.getcwd()
    os.chdir('ansible')
    google_auth_ansible_command = subprocess.run(["ansible-playbook",
                                                  "playbooks/google-authenticator.yaml",
                                                  "-i",
                                                  f"inventory/{environment}",
                                                  ]
                                                 )
    print(google_auth_ansible_command)
    bastion_users_ansible_command = subprocess.run(["ansible-playbook",
                                                     "playbooks/bastion-users.yaml",
                                                     "-i",
                                                     f"inventory/{environment}",
                                                     ]
                                                    )
    print(bastion_users_ansible_command)
    os.chdir(old_pwd)


def render_vpc_peering_mapping(environment, pulumi_stack_output):
    logging.info("Render VPC peering mapping file")
    if "external_regions" not in pulumi_stack_output:
        print(f"No external regions for: {environment} environment - skip")
        return
    vpc_peering_mapping = {
        "regions": []
    }
    for region in pulumi_stack_output.get('external_regions'):
        vpc_peering_mapping["regions"].append(
            {
                "region_name": region,
                "data": {
                    "vpc_id": pulumi_stack_output.get(f'vpc-id-{region}'),
                    "private_subnets": [
                        pulumi_stack_output.get(f'private_subnet-0-{region}'),
                        pulumi_stack_output.get(f'private_subnet-1-{region}')
                    ],
                    "public_subnets": [
                        pulumi_stack_output.get(f'public_subnet-0-{region}'),
                        pulumi_stack_output.get(f'public_subnet-1-{region}')
                    ]
                }
            }
        )
    with open(f'devops-scripts/prod/payload/{environment}-_vpc_peering_mapping.json', 'w') as fp:
        json.dump(vpc_peering_mapping, fp, sort_keys=True, indent=4)


def update_aws_kubeconfig(eks_name):
    logging.info("Get EKS cluster k8s context")
    output = subprocess.run(["aws", "eks", "update-kubeconfig", "--name", eks_name, "--profile", "prod"])
    logging.info(f'update kubeconfig - {output}')


def _load_jinja_template(folder_name, template_file):
    env = Environment(loader=FileSystemLoader(folder_name))
    template = env.get_template(template_file)
    return template


def _write_rendered_template_to_file(rendered_template, file_location):
    with open(file_location, 'w') as f:
        f.write(rendered_template)


def render_ansible_inventory_file(environment, pulumi_stack_output):
    template = _load_jinja_template('ansible', 'template-inventory.jinja2')
    rendered_template = template.render(
        neo4j_core_0=pulumi_stack_output.get('neo4j').get('Node0Ip'),
        neo4j_core_1=pulumi_stack_output.get('neo4j').get('Node1Ip'),
        neo4j_core_2=pulumi_stack_output.get('neo4j').get('Node2Ip'),
        neo4j_replica_1=pulumi_stack_output.get('neo4j').get('Replica0Ip'),
        neo4j_replica_2=pulumi_stack_output.get('neo4j').get('Replica1Ip'),
        private_key=f'{environment}-key.pem',
        bastion_host=pulumi_stack_output.get('bastion_dns_record'),
        bastion_hostname=f'{environment}-bastion'

    )
    _write_rendered_template_to_file(rendered_template, f'ansible/inventory/{environment}')


def render_lightlytics_chart(environment, pulumi_stack_output):
    logging.info("Render lightlytics chart")
    template = _load_jinja_template('charts/deployment-main',
                                    'template-production-values.yaml.jinja2')
    rendered_template = template.render(
        neo4j_dns_record=pulumi_stack_output.get('neo4j_dns_record'),
        aws_awf=pulumi_stack_output.get('aws_awf'),
        kafka_brokers=pulumi_stack_output.get('kafka_cluster_brokers_plaintext'),
        mongodb_hosts=pulumi_stack_output.get('mongodb_dns_records'),
        mongodb_backup_role=pulumi_stack_output.get('cronjob_mongo_backup_role'),
        customers_role=pulumi_stack_output.get('ms_customers_role'),
        account_role=pulumi_stack_output.get('ms_account_role'),
        changes_role=pulumi_stack_output.get('ms_changes_role')
    )
    _write_rendered_template_to_file(rendered_template,
                                     f'charts/deployment-main/values/{environment}-production-values.yaml')


def run_infrastructure_helm_charts(environment, kube_context):
    run_aws_alb_ingress_chart(environment, kube_context)
    run_external_secrets_chart(environment, kube_context)
    run_external_dns_chart(environment, kube_context)
    run_logzio_chart(environment, kube_context)


def run_aws_alb_ingress_chart(environment, kube_context):
    logging.info('install aws_alb_ingress chart')
    chart_repo_add_command = subprocess.run([
        "helm",
        "repo",
        "add",
        "incubator",
        "https://charts.helm.sh/incubator"
    ])
    logging.info(chart_repo_add_command)
    chart_install_command = subprocess.run([
        "helm",
        "upgrade",
        "--install",
        "aws-alb-ingress-controller",
        "-f",
        f"charts/infrastracture/aws-alb-ingress-controller/values/{environment}-production-values.yaml",
        "--kube-context",
        f"{kube_context}",
        "incubator/aws-alb-ingress-controller"
    ])
    logging.info(chart_install_command)


def run_external_secrets_chart(environment, kube_context):
    logging.info('install external_secrets chart')
    chart_repo_add_command = subprocess.run([
        "helm",
        "repo",
        "add",
        "external-secrets",
        "https://external-secrets.github.io/kubernetes-external-secrets"
    ])
    logging.info(chart_repo_add_command)
    chart_install_command = subprocess.run([
        "helm",
        "upgrade",
        "--install",
        "kubernetes-external-secrets",
        "--skip-crds",
        "-f",
        f"charts/infrastracture/external-secrets/values/{environment}-production-values.yaml",
        "--kube-context",
        f"{kube_context}",
        "external-secrets/kubernetes-external-secrets"
    ])
    logging.info(chart_install_command)


def run_external_dns_chart(environment, kube_context):
    logging.info('install external_dns chart')
    chart_repo_add_command = subprocess.run([
        "helm",
        "repo",
        "add",
        "bitnami",
        "https://charts.bitnami.com/bitnami"
    ])
    logging.info(chart_repo_add_command)
    chart_install_command = subprocess.run([
        "helm",
        "upgrade",
        "--install",
        "external-dns-prod",
        "--recreate-pods",
        "-f",
        f"charts/infrastracture/external-dns/values/{environment}-production-values.yaml",
        "--kube-context",
        f"{kube_context}",
        "bitnami/external-dns"
    ])
    logging.info(chart_install_command)


def run_logzio_chart(environment, kube_context):
    logging.info('install logzio chart')
    chart_repo_add_command = subprocess.run([
        "helm",
        "repo",
        "add",
        "logzio-helm",
        "https://logzio.github.io/logzio-helm/filebeat"
    ])
    logging.info(chart_repo_add_command)
    chart_install_command = subprocess.run([
        "helm",
        "upgrade",
        "--install",
        "logzio-k8s-logs",
        "--namespace",
        "kube-system",
        "-f",
        f"charts/infrastracture/logzio/values/{environment}-production-values.yaml",
        "--kube-context",
        f"{kube_context}",
        "logzio-helm/logzio-k8s-logs"
    ])
    logging.info(chart_install_command)

def render_infrastructure_helm_charts(environment, pulumi_stack_output):
    render_aws_alb_ingress_chart(environment, pulumi_stack_output)
    render_external_secrets_chart(environment, pulumi_stack_output)
    render_external_dns_chart(environment, pulumi_stack_output)
    render_logzio_chart(environment, pulumi_stack_output)


def render_aws_alb_ingress_chart(environment, pulumi_stack_output):
    logging.info("Render aws alb ingress template")
    template = _load_jinja_template('charts/infrastracture/aws-alb-ingress-controller',
                                    'template-production-values.yaml.jinja2')
    region = pulumi_stack_output.get('primaryRegion')
    rendered_template = template.render(
        region=region,
        eks_cluster=pulumi_stack_output.get('eks_cluster'),
        vpc_id=pulumi_stack_output.get(f'vpc-id-{region}'),
        alb_ingress_role_arn=pulumi_stack_output.get('alb_ingress_controller_iam_role')
    )
    _write_rendered_template_to_file(rendered_template,
                                     f'charts/infrastracture/aws-alb-ingress-controller/values/{environment}'
                                     f'-production-values.yaml')


def render_external_secrets_chart(environment, pulumi_stack_output):
    logging.info("Render external secrets template")
    template = _load_jinja_template('charts/infrastracture/external-secrets',
                                    'template-production-values.yaml.jinja2')
    rendered_template = template.render(
        region=pulumi_stack_output.get('primaryRegion'),
        external_secret_role_arn=pulumi_stack_output.get('external_secrets_role')
    )
    _write_rendered_template_to_file(rendered_template,
                                     f'charts/infrastracture/external-secrets/values/{environment}'
                                     f'-production-values.yaml')


def render_external_dns_chart(environment, pulumi_stack_output):
    logging.info("Render external dns template")
    template = _load_jinja_template('charts/infrastracture/external-dns',
                                    'template-production-values.yaml.jinja2')
    rendered_template = template.render(
        external_dns_role=pulumi_stack_output.get('external_dns_role')
    )
    _write_rendered_template_to_file(rendered_template,
                                     f'charts/infrastracture/external-dns/values/{environment}'
                                     f'-production-values.yaml')


def render_logzio_chart(environment, pulumi_stack_output):
    logging.info("Render logzio template")
    template = _load_jinja_template('charts/infrastracture/logzio',
                                    'template-production-values.yaml.jinja2')
    rendered_template = template.render(
        eks_cluster=pulumi_stack_output.get('eks_cluster')
    )
    _write_rendered_template_to_file(rendered_template,
                                     f'charts/infrastracture/logzio/values/{environment}'
                                     f'-production-values.yaml')


def get_pulumi_parameters(environment):
    logging.info(f"Get pulumi params from pulumi output file for environment:{environment}")
    pulumi_output_file = f'pulumi/lightlytics-environments/outputs/{environment}-output.json'
    if not os.path.isfile(pulumi_output_file):
        logging.error("Cannot find Pulumi output file - exit")
        sys.exit(1)
    with open(pulumi_output_file) as f:
        pulumi_stack_output = json.loads(f.read())

    return pulumi_stack_output


def store_pem_file(environment, pulumi_stack_output):
    logging.info("Store Pem file")
    key_file_path = f'{str(Path.home())}/prod-keys/{environment}-key.pem'
    with open(key_file_path, 'w') as f:
        f.write(pulumi_stack_output.get('private_key_pem'))
    os.chmod(key_file_path, stat.S_IRWXU)


def _helm_dep_up():
    old_pwd = os.getcwd()
    os.chdir('charts/deployment-main')
    helm_dep_up_command = subprocess.run([
        "helm",
        "dep",
        "up"
    ])
    logging.info(helm_dep_up_command)
    os.chdir(old_pwd)


def helm_deploy_welcome_message(environment):
    print("#######################################################")
    print(f"Congratulations on setting up Lightlytics Prod ENV: {environment}")
    print(f"front-end: http://{environment}.lightlytics.com")
    print(f"front-gate graphql api: http://{environment}.lightlytics.com/graphql")
    print(f"collection api: http://{environment}.lightlytics.com/api/v1/flowlogs")
    print("#######################################################")


def run_lightlytics_chart(environment, pulumi_stack_output, branch_and_build, kube_context):
    branch_name = branch_and_build.split('.')[0]
    build_number = branch_and_build.split('.')[1]
    render_lightlytics_chart(environment, pulumi_stack_output)
    _helm_dep_up()

    chart_install_command = subprocess.run([
        "helm",
        "upgrade",
        "--install",
        f"{environment}",
        "charts/deployment-main",
        "--set",
        f"deployment.branchName={branch_name}",
        "--set",
        f"deployment.buildNumber={build_number}",
        "--set",
        "deployment.env.ENV=prod",
        "--create-namespace",
        "--kube-context",
        f"{kube_context}",
        "-f",
        f"charts/deployment-main/values/{environment}-production-values.yaml",
        "-n",
        f"{environment}"
    ], capture_output=True)
    if chart_install_command.returncode > 0:
        logging.error(f'error from helm installation {chart_install_command.stderr}')
        sys.exit(1)

    print_file_contents(f"charts/deployment-main/values/{environment}-production-values.yaml")

    helm_deploy_welcome_message(environment)


def print_file_contents(file_path):
    with open(file_path, 'r') as f:
        print(f.read())


def production_deployment(environment,
                          render_templates_action=False,
                          store_private_key_action=False,
                          run_infra_charts_action=False,
                          run_ansible_playbooks_action=False,
                          update_k8s_context_action=False,
                          run_lightlytics_chart_action=False,
                          branch_and_build=None):
    pulumi_stack_output = get_pulumi_parameters(environment)
    if store_private_key_action and "private_key_pem" in pulumi_stack_output:
        store_pem_file(environment, pulumi_stack_output)
    if update_k8s_context_action and "eks_cluster" in pulumi_stack_output:
        update_aws_kubeconfig(pulumi_stack_output.get('eks_cluster'))
    if render_templates_action:
        render_infrastructure_helm_charts(environment, pulumi_stack_output)
        render_ansible_inventory_file(environment, pulumi_stack_output)
        render_lightlytics_chart(environment, pulumi_stack_output)
        render_vpc_peering_mapping(environment, pulumi_stack_output)
    if run_ansible_playbooks_action:
        run_bastion_ansible_playbooks(environment)
        run_neo4j_ansible_playbook(environment)
    if run_infra_charts_action:
        run_infrastructure_helm_charts(environment,
                                       pulumi_stack_output.get('eks_arn'))
    if run_lightlytics_chart_action:
        run_lightlytics_chart(environment,
                              pulumi_stack_output,
                              branch_and_build,
                              pulumi_stack_output.get('eks_arn'))


def _one_action_required_validator(args_dict, main_parser):
    for key, value in args_dict.items():
        if 'action' in key and value:
            return True
    main_parser.error('At lest one action required')


def _deploy_lightlytics_validator(args_dict, main_parser):
    if "run_lightlytics_chart_action" in args_dict.keys() and args_dict.get('run_lightlytics_chart_action'):
        if args_dict.get('branch_and_build') is not None:
            return True
        else:
            main_parser.error('On run_lightlytics_chart action branch_and_build parm must be specified')


def _parser_validator(args_dict, main_parser):
    _one_action_required_validator(args_dict, main_parser)
    _deploy_lightlytics_validator(args_dict, main_parser)


if __name__ == "__main__":
    logging.info("Start production deployment program")
    parser = argparse.ArgumentParser(
        description="Render helm chars(infrastructure & lightlytics chart) based on pulumi output - "
                    "Should be run from the main directory"
    )
    parser.add_argument(
        "--environment",
        help="The environment name - e.g: whitesource",
        required=True,
        type=str
    )
    parser.add_argument(
        "--store_private_key",
        help="Will store the pem file in the home directory",
        dest='store_private_key_action',
        action='store_true'
    )
    parser.set_defaults(store_private_key_action=False)

    parser.add_argument(
        "--run_infra_charts",
        help="Will run the infra helm charts after the render process",
        dest="run_infra_charts_action",
        action='store_true'
    )
    parser.set_defaults(run_infra_charts_action=False)

    parser.add_argument(
        "--run_lightlytics_chart",
        help="Will run the lightlytics chart",
        dest="run_lightlytics_chart_action",
        action='store_true'
    )
    parser.set_defaults(run_lightlytics_chart_action=False)

    parser.add_argument(
        "--run_ansible_playbooks",
        help="Will run ansible playbooks(bastion and neo4j)",
        dest="run_ansible_playbooks_action",
        action='store_true'
    )
    parser.set_defaults(run_ansible_playbooks_action=False)

    parser.add_argument(
        "--update_k8s_context",
        help="Will run 'aws eks update-kubeconfig' to get the cluster context",
        dest="update_k8s_context_action",
        action='store_true'
    )
    parser.set_defaults(update_k8s_context_action=False)

    parser.add_argument(
        "--render_templates",
        help="Will render all templates(helm charts values, ansible inventory and other configuration file)"
             "based on Pulumi output",
        dest="render_templates_action",
        action='store_true'
    )

    parser.add_argument(
        "--branch_and_build",
        help="The branch name And build number - e.g: master.1532",
        required=False,
        type=str
    )

    parser.set_defaults(render_templates_action=False)
    args = parser.parse_args()
    dict_args = vars(args)
    logging.info(f"Arguments: {dict_args}")
    _parser_validator(dict_args, parser)
    production_deployment(**dict_args)
