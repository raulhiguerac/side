import os
from typing import Any, BinaryIO, Dict, Optional

import boto3
from botocore.client import Config

from app.core.exceptions.storage import StorageMisconfiguredError
from app.integrations.storage.minio.mappers.error_mapper import (
    translate_storage_error,
)
from app.services.shared.schemas.storage import UploadResult


class StorageClient:
    def __init__(self) -> None:
        minio_url = os.getenv("MINIO_URL")
        access_key = os.getenv("ACCESS_KEY")
        secret_key = os.getenv("SECRET_KEY")

        if not minio_url:
            raise StorageMisconfiguredError(
                context={"missing": "MINIO_URL"}
            )

        if not access_key or not secret_key:
            raise StorageMisconfiguredError(
                context={"missing": "ACCESS_KEY/SECRET_KEY"}
            )

        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        self.client = self.session.client(
            "s3",
            endpoint_url=minio_url,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

    def upload_file(
        self,
        *,
        fileobj: BinaryIO,
        bucket: str,
        key: str,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> UploadResult:
        try:
            if hasattr(fileobj, "seek"):
                try:
                    fileobj.seek(0)
                except Exception:
                    pass

            self.client.upload_fileobj(
                Fileobj=fileobj,
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args or {},
            )

            return UploadResult(
                bucket = bucket,
                key = key
            )

        except Exception as exc:
            translate_storage_error(
                error=exc,
                operation="upload",
                bucket=bucket,
                key=key,
            )
