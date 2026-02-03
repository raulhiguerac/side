import io
import pytest
from unittest.mock import MagicMock, patch

from fastapi import UploadFile

from app.api.deps.upload_validation import validate_profile_photo_upload
from app.core.exceptions.validation import FileTooLargeError, UnsupportedFileTypeError
from app.core.files.policies import UploadPolicy


@pytest.fixture
def mock_policy():
    return UploadPolicy(
        allowed_mime_types={"image/jpeg", "image/png"},
        max_size_bytes=5 * 1024 * 1024,  # 5MB
    )


@pytest.fixture
def fake_file():
    file = MagicMock(spec=UploadFile)
    file.file = io.BytesIO(b"fake image bytes")
    return file


# Happy path - valid mime and size
@patch("app.api.deps.upload_validation.PROFILE_PHOTO_UPLOAD_POLICY")
@patch("app.api.deps.upload_validation.get_file_size")
@patch("app.api.deps.upload_validation.detect_file_mime_type")
def test_validate_profile_photo_success(
    mock_detect_mime, mock_get_size, mock_policy_obj, fake_file
):
    mock_detect_mime.return_value = "image/jpeg"
    mock_get_size.return_value = 1024  # 1KB
    mock_policy_obj.allowed_mime_types = {"image/jpeg", "image/png"}
    mock_policy_obj.max_size_bytes = 5 * 1024 * 1024

    result = validate_profile_photo_upload(file=fake_file)

    assert result == "image/jpeg"
    mock_detect_mime.assert_called_once_with(fake_file.file)
    mock_get_size.assert_called_once_with(fake_file.file)


# Unsupported mime type
@patch("app.api.deps.upload_validation.PROFILE_PHOTO_UPLOAD_POLICY")
@patch("app.api.deps.upload_validation.get_file_size")
@patch("app.api.deps.upload_validation.detect_file_mime_type")
def test_validate_profile_photo_unsupported_mime(
    mock_detect_mime, mock_get_size, mock_policy_obj, fake_file
):
    mock_detect_mime.return_value = "application/pdf"
    mock_get_size.return_value = 1024
    mock_policy_obj.allowed_mime_types = {"image/jpeg", "image/png"}
    mock_policy_obj.max_size_bytes = 5 * 1024 * 1024

    with pytest.raises(UnsupportedFileTypeError):
        validate_profile_photo_upload(file=fake_file)


# File too large
@patch("app.api.deps.upload_validation.PROFILE_PHOTO_UPLOAD_POLICY")
@patch("app.api.deps.upload_validation.get_file_size")
@patch("app.api.deps.upload_validation.detect_file_mime_type")
def test_validate_profile_photo_too_large(
    mock_detect_mime, mock_get_size, mock_policy_obj, fake_file
):
    mock_detect_mime.return_value = "image/jpeg"
    mock_get_size.return_value = 10 * 1024 * 1024  # 10MB
    mock_policy_obj.allowed_mime_types = {"image/jpeg", "image/png"}
    mock_policy_obj.max_size_bytes = 5 * 1024 * 1024  # 5MB limit

    with pytest.raises(FileTooLargeError):
        validate_profile_photo_upload(file=fake_file)


# Empty allowed_mime_types (allows all)
@patch("app.api.deps.upload_validation.PROFILE_PHOTO_UPLOAD_POLICY")
@patch("app.api.deps.upload_validation.get_file_size")
@patch("app.api.deps.upload_validation.detect_file_mime_type")
def test_validate_profile_photo_no_mime_restriction(
    mock_detect_mime, mock_get_size, mock_policy_obj, fake_file
):
    mock_detect_mime.return_value = "application/octet-stream"
    mock_get_size.return_value = 1024
    mock_policy_obj.allowed_mime_types = set()  # Empty = no restriction
    mock_policy_obj.max_size_bytes = 5 * 1024 * 1024

    result = validate_profile_photo_upload(file=fake_file)

    assert result == "application/octet-stream"
