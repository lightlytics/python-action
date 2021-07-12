import pulumi
from pulumi_aws import secretsmanager

from utils import get_resource_name_by_convention


def create_raw_json_secret(secret_name, credentials):
    name, tags = get_resource_name_by_convention(secret_name)
    pulumi_stack = pulumi.get_stack()
    created_secret = secretsmanager.Secret(
        name,
        name=f"{pulumi_stack}/{secret_name}",
        recovery_window_in_days=0
    )
    name, _ = get_resource_name_by_convention(f"{secret_name}_version")
    secretsmanager.SecretVersion(
        name,
        secret_id=created_secret.id,
        secret_string=credentials
        # opts=pulumi.ResourceOptions(ignore_changes=["secret_string"])
    )


def create_rsa_key_pair_secret(key_name, rsa_crypto_key_pair):
    pulumi_stack = pulumi.get_stack()
    name, tags = get_resource_name_by_convention(f"{key_name}_private_key_secret")
    private_key_secret = secretsmanager.Secret(
        name,
        tags=tags,
        name=f"{pulumi_stack}/{key_name}_private_key_secret",
        recovery_window_in_days=0
    )

    name, _ = get_resource_name_by_convention(f"{key_name}_private_key_secret_version")
    secretsmanager.SecretVersion(
        name,
        secret_id=private_key_secret.id,
        secret_string=rsa_crypto_key_pair.private_key_pem,
    )

    name, tags = get_resource_name_by_convention(f"{key_name}_public_key_secret")
    public_key_secret = secretsmanager.Secret(
        name,
        tags=tags,
        name=f"{pulumi_stack}/{key_name}_public_key_secret",
        recovery_window_in_days=0
    )

    name, _ = get_resource_name_by_convention(f"{key_name}_public_key_secret_version")
    secretsmanager.SecretVersion(
        name,
        secret_id=public_key_secret.id,
        secret_string=rsa_crypto_key_pair.public_key_pem,
    )