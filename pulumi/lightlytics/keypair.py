import pulumi
import pulumi_tls
from pulumi_aws import ec2

from utils import get_resource_name_by_convention


#  https://www.pulumi.com/docs/reference/pkg/tls/privatekey/
def create_keypair():
    name, tags = get_resource_name_by_convention('key')
    generated_key = pulumi_tls.PrivateKey(name, algorithm="RSA")
    ssh_key_pair = ec2.KeyPair(
        name,
        public_key=generated_key.public_key_openssh,
        key_name=name,
        tags=tags,
    )
    pulumi.export('public_key_ssh', generated_key.public_key_openssh)
    pulumi.export('private_key_pem', generated_key.private_key_pem)
    return ssh_key_pair

