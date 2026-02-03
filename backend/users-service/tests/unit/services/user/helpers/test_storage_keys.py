import uuid

from app.services.user.helpers.storage_keys import profile_photo_storage_key


def test_profile_photo_storage_key():
    account_id = uuid.UUID("c42b2c19-efda-4f42-a7e5-1e69190f51e0")

    result = profile_photo_storage_key(account_id)

    assert result == "accounts/c42b2c19-efda-4f42-a7e5-1e69190f51e0/profile/photo"


def test_profile_photo_storage_key_different_id():
    account_id = uuid.UUID("12345678-1234-1234-1234-123456789abc")

    result = profile_photo_storage_key(account_id)

    assert result == "accounts/12345678-1234-1234-1234-123456789abc/profile/photo"
