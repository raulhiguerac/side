from fastapi import UploadFile

from app.core.files.policies import NEIGHBORHOOD_GEOMETRY_UPLOAD_POLICY, NEIGHBORHOOD_BULK_UPLOAD_POLICY
from app.core.files.validators import get_file_size, validate_file_extension
from app.core.exceptions.validation import FileTooLargeError


def _validate_upload(file: UploadFile, policy) -> None:
    try:
        validate_file_extension(file.filename, policy.allowed_extensions)

        size = get_file_size(file.file)
        if size > policy.max_size_bytes:
            raise FileTooLargeError(
                context={"size_bytes": size, "max_bytes": policy.max_size_bytes}
            )
    finally:
        file.file.seek(0)


def validate_neighborhood_geometry_upload(file: UploadFile) -> None:
    _validate_upload(file, NEIGHBORHOOD_GEOMETRY_UPLOAD_POLICY)


def validate_neighborhood_bulk_upload(file: UploadFile) -> None:
    _validate_upload(file, NEIGHBORHOOD_BULK_UPLOAD_POLICY)
