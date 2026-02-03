import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.common import Principal
from app.services.user.schemas.current import CurrentUserOut
from app.services.user.schemas.photo import PhotoUploadOut
from app.services.user.use_cases.profile.upload_profile_photo import UpdateCurrentProfilePhotoUseCase


@pytest.fixture
def principal():
    return Principal(
        sub=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        email_verified=True,
        scope=["users-ms"],
    )


@pytest.fixture
def uow():
    return AsyncMock()


@pytest.fixture
def cache_client():
    return AsyncMock()


@pytest.fixture
def storage_client():
    return AsyncMock()


@pytest.fixture
def account_reader():
    return AsyncMock()


@pytest.fixture
def profile_reader():
    return AsyncMock()


@pytest.fixture
def uc(uow, cache_client, storage_client, account_reader, profile_reader):
    return UpdateCurrentProfilePhotoUseCase(
        uow=uow,
        cache_client=cache_client,
        storage_client=storage_client,
        account_reader=account_reader,
        profile_reader=profile_reader,
        bucket_name="test-bucket",
        base_url="https://storage.example.com",
    )


@pytest.fixture
def current_account(principal):
    return CurrentUserOut(
        account_id=principal.sub,
        email=principal.email,
        account_type="person",
        onboarding_step="intent",
        is_active=True,
    )


@pytest.fixture
def profile_db():
    profile = MagicMock()
    profile.photo_url = None
    profile.photo_key = None
    return profile


@pytest.fixture
def fake_file():
    return io.BytesIO(b"fake image bytes")


# Happy path
@pytest.mark.asyncio
async def test_upload_photo_success(
    uc, principal, uow, cache_client, storage_client, account_reader, profile_reader,
    current_account, profile_db, fake_file
):
    content_type = "image/jpeg"

    account_reader.get_active.return_value = current_account
    profile_reader.get_model.return_value = profile_db
    storage_client.upload_file.return_value = None
    uow.commit.return_value = None
    cache_client.delete.return_value = None

    result = await uc.execute(file=fake_file, content_type=content_type, principal=principal)

    account_reader.get_active.assert_awaited_once_with(account_id=principal.sub)
    profile_reader.get_model.assert_awaited_once()
    storage_client.upload_file.assert_awaited_once()
    uow.commit.assert_awaited_once()
    cache_client.delete.assert_awaited_once()

    # Profile should have photo url and key set
    assert profile_db.photo_url is not None
    assert profile_db.photo_key is not None

    assert isinstance(result, PhotoUploadOut)
    assert result.photo_url is not None


# Storage upload fails
@pytest.mark.asyncio
async def test_upload_photo_storage_fails(
    uc, principal, uow, storage_client, account_reader, profile_reader,
    current_account, profile_db, fake_file
):
    content_type = "image/jpeg"

    account_reader.get_active.return_value = current_account
    profile_reader.get_model.return_value = profile_db
    storage_client.upload_file.side_effect = Exception("Storage error")

    with pytest.raises(Exception, match="Storage error"):
        await uc.execute(file=fake_file, content_type=content_type, principal=principal)

    uow.commit.assert_not_called()
