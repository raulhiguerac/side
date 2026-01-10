from fastapi import UploadFile

from app.core.files.policies import PROFILE_PHOTO_UPLOAD_POLICY
from app.core.files.validators import detect_file_mime_type, get_file_size

from app.core.exceptions.validation import FileTooLargeError, UnsupportedFileTypeError

def validate_profile_photo_upload(upload_file: UploadFile):
    policy = PROFILE_PHOTO_UPLOAD_POLICY

    mime = detect_file_mime_type(upload_file.file)
    size = get_file_size(upload_file.file)

    if policy.allowed_mime_types and mime not in policy.allowed_mime_types:
        raise UnsupportedFileTypeError(
            context={"detected_mime": mime}
        )

    if size > policy.max_size_bytes:
        raise FileTooLargeError(
            context={"size": size, "max": policy.max_size_bytes}
        )

    return None
