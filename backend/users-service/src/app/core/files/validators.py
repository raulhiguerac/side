import filetype

from typing import BinaryIO

from app.core.exceptions.validation import UnsupportedFileTypeError

def get_file_size(file: BinaryIO):
    try:
        current_pos = file.tell()
    except Exception as e:
        raise RuntimeError("File stream must be seekable/tellable") from e
    
    try:
        file.seek(0, 2) 
        size = file.tell()
        return size
    
    finally:
        file.seek(current_pos)

def detect_file_mime_type(file: BinaryIO) -> str:
    try:
        current_pos = file.tell()
    except Exception as e:
        raise RuntimeError("File stream must be seekable/tellable") from e

    try:
        file.seek(0)
        header = file.read(261)

        kind = filetype.guess(header)
        if kind is None:
            raise UnsupportedFileTypeError(
                context={
                    "detected_mime": None,
                    "header_bytes_read": len(header),
                }
            )

        return kind.mime.lower()
    finally:
        file.seek(current_pos)