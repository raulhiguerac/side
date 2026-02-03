import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import TypeAdapter

from app.models.account import AccountIntent
from app.schemas.common import Principal
from app.services.user.schemas.current import CurrentUserOut, CurrentUserProfileOut
from app.services.user.schemas.update import UpdateRequest
from app.services.user.use_cases.profile.update_current_profile import UpdateCurrentProfileUseCase


PROFILE_DATA = {
    "first_name": "pepito",
    "last_name": "perez",
    "phone": "1234567890",
    "photo_url": "https://s3.example.com/photo.jpg",
    "description": "Old description",
    "intent": AccountIntent.buyer,
    "account_type": "person",
}

PROFILE_ADAPTER = TypeAdapter(CurrentUserProfileOut)
UPDATE_ADAPTER = TypeAdapter(UpdateRequest)


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
def account_reader():
    return AsyncMock()


@pytest.fixture
def profile_reader():
    return AsyncMock()


@pytest.fixture
def uc(uow, cache_client, account_reader, profile_reader):
    return UpdateCurrentProfileUseCase(
        uow=uow,
        cache_client=cache_client,
        account_reader=account_reader,
        profile_reader=profile_reader,
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
    profile.first_name = "pepito"
    profile.last_name = "perez"
    profile.phone = "1234567890"
    profile.photo_url = "https://s3.example.com/photo.jpg"
    profile.description = "Old description"
    profile.intent = AccountIntent.buyer
    return profile


# Happy path
@pytest.mark.asyncio
async def test_update_profile_success(
    uc, principal, uow, cache_client, account_reader, profile_reader, current_account, profile_db
):
    req = UPDATE_ADAPTER.validate_python({
        "phone": "0987654321",
        "description": "New description",
        "account_type": "person",
    })

    account_reader.get_active.return_value = current_account
    profile_reader.get_model.return_value = profile_db
    uow.commit.return_value = None
    cache_client.delete.return_value = None
    cache_client.set.return_value = None

    result = await uc.execute(principal=principal, req=req)

    account_reader.get_active.assert_awaited_once_with(account_id=principal.sub)
    profile_reader.get_model.assert_awaited_once()
    uow.commit.assert_awaited_once()

    # Profile should be updated
    assert profile_db.phone == "0987654321"
    assert profile_db.description == "New description"

    # Cache should be invalidated and set
    cache_client.delete.assert_awaited_once()
    cache_client.set.assert_awaited_once()

    assert isinstance(result, CurrentUserProfileOut)


# Commit fails - rollback
@pytest.mark.asyncio
async def test_update_profile_commit_fails(
    uc, principal, uow, cache_client, account_reader, profile_reader, current_account, profile_db
):
    req = UPDATE_ADAPTER.validate_python({
        "phone": "0987654321",
        "account_type": "person",
    })

    account_reader.get_active.return_value = current_account
    profile_reader.get_model.return_value = profile_db
    uow.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        await uc.execute(principal=principal, req=req)

    uow.rollback.assert_awaited_once()
    cache_client.delete.assert_not_called()
