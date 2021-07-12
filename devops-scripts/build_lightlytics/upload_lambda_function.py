#!/usre/bin/python
import boto3
import zipfile
import os
import shutil

S3_BUCKET_NAME = "lightlytics-lambda-functions"
BUILD_NUMBER = os.getenv('BUILD_NUMBER', "1")
LAMBDA_DIR = "lightlytics/lambda_functions"


def upload_function_to_s3(bucket_name, zip_file_name, function_name):
    print("Upload  file: {} to bucket: {}".format(zip_file_name, bucket_name))
    s3 = boto3.client('s3')
    s3.upload_file(
        zip_file_name, bucket_name, function_name + "/" + zip_file_name
    )


def zip_lambda_function(folder_name_path, function_name, zip_file_name):
    print("Create zip file - zip_file_name: {}".format(zip_file_name))
    saved_path = os.getcwd()
    os.chdir(folder_name_path)
    zip_file = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('.'):
        for file in files:
            if not file.endswith('.zip'):
                zip_file.write(os.path.join(root, file))
    zip_file.close()
    shutil.move(zip_file_name, saved_path)
    os.chdir(saved_path)


def lambda_update_function(bucket_name, function_name, zip_file_name):
    print(
        "Update lambda: {}  code from bucket: s3:{}".format(
            function_name, bucket_name
        )
    )
    lambda_function = boto3.client('lambda')
    lambda_function.update_function_code(
        FunctionName=function_name,
        S3Bucket=bucket_name,
        S3Key='{}/{}'.format(function_name, zip_file_name)
    )


if __name__ == "__main__":
    base_dir = LAMBDA_DIR
    ignored_functions = [
        "lightlytics-collector", "template.yaml", "lightlytics-initializer",
        "lightlytics-collector"
    ]
    lambda_functions = [
        x for x in os.listdir(base_dir) if x not in ignored_functions
    ]
    for lambda_function in lambda_functions:
        function_path = "{}/{}".format(base_dir, lambda_function)
        zip_file_name = lambda_function + ".zip"
        zip_lambda_function(function_path, lambda_function, zip_file_name)
        upload_function_to_s3(S3_BUCKET_NAME, zip_file_name, lambda_function)
        os.remove(zip_file_name)
        lambda_update_function(S3_BUCKET_NAME, lambda_function, zip_file_name)
