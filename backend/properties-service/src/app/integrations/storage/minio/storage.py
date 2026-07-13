import os

import boto3
from botocore.client import Config

from app.core.exceptions.storage import StorageMisconfiguredError
from app.integrations.storage.minio.mappers.error_mapper import translate_storage_error


class StorageClient:
    def __init__(self) -> None:
        minio_url = os.getenv("MINIO_URL")
        access_key = os.getenv("ACCESS_KEY_PROPERTIES")
        secret_key = os.getenv("SECRET_KEY_PROPERTIES")

        if not minio_url:
            raise StorageMisconfiguredError(context={"missing": "MINIO_URL"})

        if not access_key or not secret_key:
            raise StorageMisconfiguredError(context={"missing": "ACCESS_KEY_PROPERTIES/SECRET_KEY_PROPERTIES"})

        public_url = os.getenv("STORAGE_PUBLIC_BASE_URL", minio_url).rstrip("/")

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self.client = session.client(
            "s3",
            endpoint_url=minio_url,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )
        # Cliente separado para presigned URLs — firma con el host público
        # para que el browser pueda hacer el PUT directamente sin signature mismatch
        self._presign_client = session.client(
            "s3",
            endpoint_url=public_url,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

    def generate_presigned_put_url(self, *, bucket: str, key: str, ttl: int) -> str:
        try:
            return self._presign_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=ttl,
            )
        except Exception as exc:
            translate_storage_error(error=exc, operation="presign", bucket=bucket, key=key)
