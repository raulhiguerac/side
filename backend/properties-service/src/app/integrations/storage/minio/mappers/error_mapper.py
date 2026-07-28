from typing import Literal, NoReturn

from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    NoCredentialsError,
    ParamValidationError,
    PartialCredentialsError,
    ReadTimeoutError,
)

from app.core.exceptions.storage import (
    BucketNotFoundError,
    StorageAccessDeniedError,
    StorageInvalidRequestError,
    StorageMisconfiguredError,
    StoragePresignFailedError,
    StorageUnavailableError,
)


def translate_storage_error(
    *,
    error: Exception,
    operation: Literal["presign", "delete", "head", "get"],
    bucket: str,
    key: str | None = None,
) -> NoReturn:
    if isinstance(
        error,
        (
            ReadTimeoutError,
            ConnectTimeoutError,
            ConnectionClosedError,
            EndpointConnectionError,
        ),
    ):
        raise StorageUnavailableError(
            cause=error,
            context={"bucket": bucket, "object": key, "operation": operation},
        ) from error

    if isinstance(error, (NoCredentialsError, PartialCredentialsError)):
        raise StorageMisconfiguredError(
            cause=error,
            context={"bucket": bucket, "operation": operation},
        ) from error

    if isinstance(error, ParamValidationError):
        raise StorageInvalidRequestError(
            cause=error,
            context={"bucket": bucket, "object": key, "operation": operation},
        ) from error

    if isinstance(error, ClientError):
        code = (error.response.get("Error", {}) or {}).get("Code")

        if code in ("NoSuchBucket", "InvalidBucketName", "AllAccessDisabled"):
            raise BucketNotFoundError(
                context={"bucket": bucket, "operation": operation},
                cause=error,
            ) from error

        if code in ("AccessDenied", "UnauthorizedOperation"):
            raise StorageAccessDeniedError(
                context={"bucket": bucket, "object": key, "operation": operation},
                cause=error,
            ) from error

    raise StoragePresignFailedError(
        context={
            "bucket": bucket,
            "object": key,
            "operation": operation,
            "hint": type(error).__name__,
        },
        cause=error,
    ) from error
