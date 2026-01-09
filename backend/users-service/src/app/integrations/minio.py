import os
import boto3

from botocore.client import Config

class MinioIntegration:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id = os.getenv('ACCESS_KEY'),
            aws_secret_access_key = os.getenv('SECRET_KEY')
        )
        self.client = self.session.client(
            's3',
            endpoint_url=os.getenv('MINIO_URL'),
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )