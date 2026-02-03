import uuid
import pytest
from unittest.mock import AsyncMock
from pydantic import TypeAdapter

from app.models.account import AccountIntent
from app.services.user.schemas.current import CurrentUserProfileOut
from app.services.user.use_cases.profile.get_current_profile import GetCurrentProfileUseCase


PROFILE_DATA = {
    "first_name": "pepito",
    "last_name": "perez",
    "phone": "1234567890",
    "photo_url": "https://s3.example.com/photo.jpg",
    "description": "Test description",
    "intent": AccountIntent.buyer,
    "account_type": "person",
}

PROFILE_ADAPTER = TypeAdapter(CurrentUserProfileOut)


@pytest.fixture
def profile_service():
    return AsyncMock()


@pytest.fixture
def uc(profile_service):
    return GetCurrentProfileUseCase(profile_service=profile_service)


@pytest.fixture
def mock_profile_out():
    return PROFILE_ADAPTER.validate_python({"profile": PROFILE_DATA})


# Happy path
@pytest.mark.asyncio
async def test_get_current_profile_success(uc, profile_service, mock_profile_out):
    account_id = uuid.uuid4()
    profile_service.get_active_profile.return_value = mock_profile_out

    result = await uc.execute(account_id=account_id)

    profile_service.get_active_profile.assert_awaited_once_with(account_id=account_id)
    assert result == mock_profile_out
    assert isinstance(result, CurrentUserProfileOut)
