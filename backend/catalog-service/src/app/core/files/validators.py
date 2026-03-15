import os
from typing import BinaryIO

from app.core.exceptions.validation import UnsupportedFileTypeError


def get_file_size(file: BinaryIO) -> int:
    current_pos = file.tell()
    try:
        file.seek(0, 2)
        return file.tell()
    finally:
        file.seek(current_pos)


def validate_file_extension(filename: str, allowed_extensions: set[str]) -> str:
    _, ext = os.path.splitext(filename.lower())
    if ext not in allowed_extensions:
        raise UnsupportedFileTypeError(
            context={"extension": ext, "allowed": list(allowed_extensions)}
        )
    return ext
