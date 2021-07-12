import json, re

import pulumi
from pulumi_aws import eks, iam, ec2

from utils import get_resource_name_by_convention, create_eks_oidc_thumbprint

conf = pulumi.Config()
PLACE_HOLDER_FOR_OIDC_ARN = "PLACE_HOLDER_FOR_OIDC_ARN"
PLACE_HOLDER_FOR_OIDC_URL_WITH_AUD_SUFFIX = "PLACE_HOLDER_FOR_OIDC_URL_WITH_AUD_SUFFIX"
PLACE_HOLDER_FOR_OIDC_URL_WITH_SUB_SUFFIX = "PLACE_HOLDER_FOR_OIDC_URL_WITH_SUB_SUFFIX"
PLACE_HOLDER_FOR_OIDC_SERVICE_ACCOUNT_SUB = "PLACE_HOLDER_FOR_OIDC_SERVICE_ACCOUNT_SUB"
ASSUME_ROLE_POLICY_KEY = 'assume_role_policy'


# todo(zeev+dan): make the cluster auto-add zeev + dan + other admins (Auto)
# See - https://docs.aws.amazon.com/eks/latest/userguide/create-public-private-vpc.html
# We deploy 2 Public + 2 Private Subnets as recommended, no need to add more atm
def create_eks_cluster(vpc, public_subnets, private_subnets, keypair, iam_polices):
    eks_cluster_iam_role = create_eks_sts_assume_role_policy()
    control_plane_security_group = create_eks_control_plane_security_group(vpc)

    name, tags = get_resource_name_by_convention('eks_cluster')
    eks_cluster = eks.Cluster(
        name,
        tags=tags,
        name=name,
        version="1.19",
        vpc_config=eks.ClusterVpcConfigArgs(
            subnet_ids=public_subnets[:2] + private_subnets[:2],
            security_group_ids=[control_plane_security_group.id]
        ),
        role_arn=eks_cluster_iam_role.arn,
        enabled_cluster_log_types=[
            "api", "audit", "authenticator", "controllerManager", "scheduler"
        ]
    )
    eks_cluster_node_group_iam_role = create_eks_cluster_nodes_iam_role()
    name, tags = get_resource_name_by_convention('node_group')
    cluster_conf = conf.require_object("EksClusterConf")
    node_group = eks.NodeGroup(
        name,
        tags=tags,
        cluster_name=eks_cluster.name,
        instance_types=cluster_conf['EksClusterInstanceTypes'],
        node_group_name=name,
        disk_size=250,
        node_role_arn=eks_cluster_node_group_iam_role.arn,
        subnet_ids=private_subnets[:2],
        scaling_config=eks.NodeGroupScalingConfigArgs(
            desired_size=4, max_size=4, min_size=4
        ),
        remote_access=eks.NodeGroupRemoteAccessArgs(
            ec2_ssh_key=keypair.key_name
        )
    )

    open_id_connect = create_cluster_open_id_connect_provider(eks_cluster)
    sts_eks_oidc_trust_relationship_policy = create_oidc_eks_trust_relationship_policy(open_id_connect)

    # https://aws.amazon.com/blogs/containers/introducing-amazon-eks-add-ons/
    kube_system_assume_role_policy = create_oidc_eks_service_account_policy(open_id_connect)

    external_dns_service_account_sub = "system:serviceaccount:default:external-dns-prod"
    external_dns_service_assume_role_policy = create_oidc_eks_service_account_policy(open_id_connect,
                                                                                     external_dns_service_account_sub)

    roles_to_create = [
        {"name": "kube_system_role", ASSUME_ROLE_POLICY_KEY: kube_system_assume_role_policy},
        {"name": "alb_ingress_controller_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
        {"name": "external_dns_role", ASSUME_ROLE_POLICY_KEY: external_dns_service_assume_role_policy},
        {"name": "external_secrets_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
        {"name": "ms_account_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
        {"name": "ms_customers_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
        {"name": "ms_changes_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
        {"name": "cronjob_mongo_backup_role", ASSUME_ROLE_POLICY_KEY: sts_eks_oidc_trust_relationship_policy},
    ]
    created_roles = {}
    for i, role_to_create in enumerate(roles_to_create):
        name = role_to_create['name']
        resource_name, _ = get_resource_name_by_convention(name)
        created_roles[name] = iam.Role(
            resource_name,
            name=resource_name,
            assume_role_policy=role_to_create[ASSUME_ROLE_POLICY_KEY],
        )

    attach_eks_cluster_role_policies(created_roles)
    attach_ms_accounts_service_role_policies(created_roles, iam_polices)
    attach_customers_service_role_policies(created_roles, iam_polices)
    attach_ms_changes_role_policies(created_roles, iam_polices)
    attach_alb_ingress_controller_role_policies(created_roles, iam_polices)
    attach_external_secrets_service_role_policies(created_roles, iam_polices)
    attach_external_dns_role_policies(created_roles, iam_polices)
    attach_cron_mongo_backup_role_policy(created_roles, iam_polices)
    #
    pulumi.export("eks_node_group", node_group.id)
    pulumi.export('eks_cluster', eks_cluster.id)
    pulumi.export("eks_arn", eks_cluster.arn)
    #
    return eks_cluster, open_id_connect


def create_eks_control_plane_security_group(vpc):
    # security group applied to ENI that is attached to EKS Control Plane master nodes, as well as any managed workloads
    # NOTE: this is empty intentionally (eksctl does the same)
    return ec2.SecurityGroup(
        "ControlPlaneSecurityGroup", vpc_id=vpc.id
    )


# https://docs.aws.amazon.com/eks/latest/userguide/service_IAM_role.html
def create_eks_sts_assume_role_policy():
    name, tags = get_resource_name_by_convention('eks_cluster_iam_role')
    # Create EKS IAM role
    with open('polices/eks_assume_role_policy.json') as f:
        eks_assume_role_policy_document = json.load(f)

        eks_cluster_iam_role = iam.Role(
            name,
            assume_role_policy=json.dumps(eks_assume_role_policy_document),
            tags=tags
        )

        name, _ = get_resource_name_by_convention('eks_cluster_iam_role_policy_attachment')
        iam.RolePolicyAttachment(
            name,
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
            role=eks_cluster_iam_role.name
        )
        name, _ = get_resource_name_by_convention('eks_cluster_iam_role_policy_attachment_sg_for_pods_policy')
        iam.RolePolicyAttachment(
            name,
            # Enabled Security groups for pods - Reference:
            # https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSVPCResourceController",
            role=eks_cluster_iam_role.name
        )
        pulumi.export('eks_cluster_iam_role', eks_cluster_iam_role.arn)

        return eks_cluster_iam_role


def create_eks_cluster_nodes_iam_role():
    with open('polices/assume_role_policy.json') as f:
        eks_node_group_assume_role_policy = json.load(f)

        name, tags = get_resource_name_by_convention('eks_cluster_node_group_iam_role')
        eks_cluster_node_group_iam_role = iam.Role(
            name,
            tags=tags,
            assume_role_policy=json.dumps(eks_node_group_assume_role_policy)
        )

        name, _ = get_resource_name_by_convention('eks_cluster_node_group_policy_attachment_AmazonEKSWorkerNodePolicy')
        iam.RolePolicyAttachment(
            name,
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
            role=eks_cluster_node_group_iam_role.name
        )

        name, _ = get_resource_name_by_convention(
            'eks_cluster_node_group_policy_attachment_AmazonEC2ContainerRegistryReadOnly')
        iam.RolePolicyAttachment(
            name,
            policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
            role=eks_cluster_node_group_iam_role.name
        )

        name, _ = get_resource_name_by_convention('eks_cluster_node_group_policy_attachment_AmazonEKS_CNI_Policy')
        iam.RolePolicyAttachment(
            name,
            policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
            role=eks_cluster_node_group_iam_role.name
        )
        pulumi.export('eks_cluster_node_group_iam_role', eks_cluster_node_group_iam_role.arn)

        return eks_cluster_node_group_iam_role


def create_cluster_open_id_connect_provider(eks_cluster):
    name, _ = get_resource_name_by_convention('cluster_open_id_connect_provider')
    lightlytics_cluster_open_id_connect_provider = iam.OpenIdConnectProvider(
        name,
        client_id_lists=['sts.amazonaws.com'],
        thumbprint_lists=[create_eks_oidc_thumbprint()],
        url=eks_cluster.identities[0].oidcs[0].issuer
    )
    pulumi.export("lightlytics_cluster_open_id_connect_provider_arn", lightlytics_cluster_open_id_connect_provider.arn)
    pulumi.export("lightlytics_cluster_open_id_connect_provider_url", lightlytics_cluster_open_id_connect_provider.url)
    return lightlytics_cluster_open_id_connect_provider


def create_oidc_eks_trust_relationship_policy(open_id_connect):
    with open('./polices/assume_role_with_web_identity_policy.json') as f:
        policy_document = f.read()
        file_split = re.split(f"{PLACE_HOLDER_FOR_OIDC_URL_WITH_AUD_SUFFIX}|{PLACE_HOLDER_FOR_OIDC_ARN}",
                              policy_document)
        oidc_aud = pulumi.Output.concat(open_id_connect.url, ":aud")
        policy = pulumi.Output.concat(file_split[0], open_id_connect.arn, file_split[1], oidc_aud, file_split[2])
        return policy


def create_oidc_eks_service_account_policy(open_id_connect, oidc_sub_name="system:serviceaccount:kube-system:aws-node"):
    with open('./polices/assume_role_with_web_identity_service_account_policy.json') as f:
        policy_document = f.read()
        file_split = re.split(
            f"{PLACE_HOLDER_FOR_OIDC_URL_WITH_SUB_SUFFIX}|{PLACE_HOLDER_FOR_OIDC_SERVICE_ACCOUNT_SUB}|{PLACE_HOLDER_FOR_OIDC_ARN}",
            policy_document)
        oidc_sub = pulumi.Output.concat(open_id_connect.url, ':sub')
        policy = pulumi.Output.concat(file_split[0], open_id_connect.arn, file_split[1], oidc_sub, file_split[2],
                                      oidc_sub_name, file_split[3])
        return policy


def attach_eks_cluster_role_policies(service_accounts_roles):
    role = service_accounts_roles['kube_system_role']
    name, _ = get_resource_name_by_convention('kube_system_policy_attachment')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
    )


def attach_customers_service_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['ms_customers_role']

    name, _ = get_resource_name_by_convention('ses_to_ms_customers_attach_policy')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('ses_policy').arn
    )
    name, _ = get_resource_name_by_convention('sqs_to_ms_customers_attach_policy')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('sqs_policy').arn
    )
    pulumi.export("ms_customers_role", role.arn)


def attach_ms_accounts_service_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['ms_account_role']

    name, _ = get_resource_name_by_convention('s3_to_ms_account_attach_policy')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('s3_iam_policy').arn
    )

    name, _ = get_resource_name_by_convention('describe_regions_to_ms_account_attach_policy')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('describe_regions_policy').arn
    )

    name, _ = get_resource_name_by_convention('sts_to_ms_account_attach_policy')
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('sts_policy')
    )
    pulumi.export("ms_account_role", role.arn)


def attach_ms_changes_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['ms_changes_role']

    name, _ = get_resource_name_by_convention("sqs_messages_to_ms_changes_attach_policy")
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('sqs_messages_policy').arn
    )

    pulumi.export("ms_changes_role", role.arn)


def attach_alb_ingress_controller_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['alb_ingress_controller_role']

    name, _ = get_resource_name_by_convention("alb_ingress_controller_attach_policy")
    iam.RolePolicyAttachment(
        name,
        role=role,
        policy_arn=iam_polices.get('alb_ingress_controller_policy').arn
    )
    pulumi.export("alb_ingress_controller_iam_role", role.arn)


def attach_external_secrets_service_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['external_secrets_role']

    name, _ = get_resource_name_by_convention("external_secrets_attach_policy_secret_manager")
    iam.RolePolicyAttachment(
        name,
        role=role,
        policy_arn=iam_polices.get('secret_manager_policy')
    )

    name, _ = get_resource_name_by_convention("external_secrets_attach_policy_ssm")
    iam.RolePolicyAttachment(
        name,
        role=role,
        policy_arn=iam_polices.get('ssm_policy').arn
    )
    pulumi.export("external_secrets_role", role.arn)


def attach_external_dns_role_policies(service_accounts_roles, iam_polices):
    role = service_accounts_roles['external_dns_role']

    name, _ = get_resource_name_by_convention("external_dns_attach_policy")
    iam.RolePolicyAttachment(
        name,
        role=role,
        policy_arn=iam_polices.get('external_dns_policy').arn
    )
    pulumi.export("external_dns_role", role.arn)


def attach_cron_mongo_backup_role_policy(service_accounts_roles, iam_polices):
    role = service_accounts_roles['cronjob_mongo_backup_role']
    name, _ = get_resource_name_by_convention("s3_to_cronjob_mongo_backups")
    iam.RolePolicyAttachment(
        name,
        role=role.name,
        policy_arn=iam_polices.get('s3_iam_mongo_policy')
    )
    pulumi.export("cronjob_mongo_backup_role", role.arn)

