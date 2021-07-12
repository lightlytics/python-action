import json
import pulumi
from secrets import create_raw_json_secret
from utils import get_resource_name_by_convention, get_lightlytics_com_route53_zone, \
    get_route53_record_name_by_convention
config = pulumi.Config()
LIGHTLYTICS_SUPPORT_USER_PASSWORD_PLACEHOLDER = "LIGHTLYTICS_SUPPORT_USER_PASSWORD_PLACEHOLDER"
LIGHTLYTICS_SUPPORT_USER_EMAIL = "devops@lightlytics.com"


#TODO : united to one function
def create_lightlytics_support_user_credentials(secret_name="lightlytics_support_user"):
    support_user_password = config.require_secret('lightlyticsSupportPassword')
    support_user_credentials_serialized = json.dumps({
        "username": LIGHTLYTICS_SUPPORT_USER_EMAIL,
        "password": LIGHTLYTICS_SUPPORT_USER_PASSWORD_PLACEHOLDER
    })
    temp = support_user_credentials_serialized.split(LIGHTLYTICS_SUPPORT_USER_PASSWORD_PLACEHOLDER)
    mongo_credentials = pulumi.Output.concat(temp[0], support_user_password, temp[1])
    create_raw_json_secret(secret_name, mongo_credentials)
    return LIGHTLYTICS_SUPPORT_USER_EMAIL, support_user_password
