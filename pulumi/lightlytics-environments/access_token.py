import pulumi_tls as tls

from secrets import create_rsa_key_pair_secret
from utils import get_resource_name_by_convention


def create_access_token():
    name, _ = get_resource_name_by_convention("access_token_key")
    access_token_key = tls.PrivateKey(
        name,
        algorithm="RSA",
        rsa_bits=4096
    )

    key_name = "access_token"
    create_rsa_key_pair_secret(key_name, access_token_key)
