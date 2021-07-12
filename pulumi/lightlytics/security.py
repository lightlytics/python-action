import pulumi
from pulumi_aws import iam, accessanalyzer
from utils import get_resource_name_by_convention


def set_lightlytics_security_polices():
    _set_password_policy()
    _set_access_analyzer()


def _set_password_policy():
    name, _ = get_resource_name_by_convention("password_policy")
    password_policy = iam.AccountPasswordPolicy(
        name,
        minimum_password_length=15,
        require_numbers=True,
        require_symbols=True,
        require_lowercase_characters=True,
        require_uppercase_characters=True,
        password_reuse_prevention=24
    )


def _set_access_analyzer():
    name, tags = get_resource_name_by_convention('access_analyzer')
    access_analyzer = accessanalyzer.Analyzer(name,
                                              analyzer_name=name
    )


