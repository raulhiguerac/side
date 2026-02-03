import pytest
from unittest.mock import AsyncMock

from app.services.auth.use_cases.logout import LogoutUseCase


@pytest.fixture
def auth_provider():
    return AsyncMock()


@pytest.fixture
def uc(auth_provider):
    return LogoutUseCase(auth_provider=auth_provider)


# With refresh token
@pytest.mark.asyncio
async def test_logout_with_refresh_token(uc, auth_provider):
    refresh_token = "valid_refresh_token"

    auth_provider.logout.return_value = None

    await uc.logout(refresh_token=refresh_token)

    auth_provider.logout.assert_awaited_once_with(refresh_token=refresh_token)


# Without refresh token (idempotent)
@pytest.mark.asyncio
async def test_logout_without_refresh_token(uc, auth_provider):
    await uc.logout(refresh_token=None)

    auth_provider.logout.assert_not_called()
