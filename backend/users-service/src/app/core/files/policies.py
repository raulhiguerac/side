import os
from typing import Set
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadPolicy:
    """
    Describe las reglas que debe cumplir un archivo subido.
    """
    allowed_mime_types: Set[str]
    max_size_bytes: int

def _parse_mime_types(env_var: str) -> Set[str]:
    if not env_var:
        return set()

    return {
        mime.strip().lower()
        for mime in env_var.split(',')
        if mime.strip()
    }

PROFILE_PHOTO_UPLOAD_POLICY = UploadPolicy(
    allowed_mime_types=_parse_mime_types(
        os.getenv("ACCEPTED_IMAGE_MIME_TYPES")
    ),
    max_size_bytes=5 * 1024 * 1024,
)