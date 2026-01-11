import os
import boto3
from typing import Any, BinaryIO, Dict, Optional

from botocore.client import Config
from botocore.exceptions import (
    ReadTimeoutError,
    ConnectTimeoutError,
    ConnectionClosedError,
    EndpointConnectionError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    ParamValidationError,
)

from app.core.exceptions.storage import (
    BucketNotFoundError,
    StorageUnavailableError,
    StorageUploadFailedError,
    StorageAccessDeniedError,
    StorageMisconfiguredError,
    StorageInvalidRequestError
)


class StorageClient:
    def __init__(self):
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
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def upload_file(
            self, 
            fileobj: BinaryIO,
            bucket: str,
            key: str,
            extra_args: Optional[Dict[str, Any]] = None
        ):
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
                ExtraArgs=extra_args or {}
            )

            return {"bucket": bucket, "key": key}

        except (
            ReadTimeoutError,
            ConnectTimeoutError,
            ConnectionClosedError,
            EndpointConnectionError,
        ) as e:
            raise StorageUnavailableError(
                cause=e,
                context={"bucket": bucket, "object": key},
            )

        except (NoCredentialsError, PartialCredentialsError) as e:
            raise StorageMisconfiguredError(
                cause=e,
                context={"bucket": bucket},
            )

        except ParamValidationError as e:
            raise StorageInvalidRequestError(
                cause=e,
                context={"bucket": bucket, "object": key},
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code in ("NoSuchBucket", "InvalidBucketName", "AllAccessDisabled"):
                raise BucketNotFoundError(
                    context={"bucket": bucket},
                    cause=e,
                )

            if error_code in ("AccessDenied", "UnauthorizedOperation"):
                raise StorageAccessDeniedError(
                    context={"bucket": bucket, "object": key},
                    cause=e,
                )

            raise StorageUploadFailedError(
                context={"bucket": bucket, "object": key, "s3_code": error_code},
                cause=e,
            )
        except Exception as e: 
            raise StorageUploadFailedError(
                context={"bucket": bucket, "object": key, "hint": type(e).__name__},
                cause=e,
            )