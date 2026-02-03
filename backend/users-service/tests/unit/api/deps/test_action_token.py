import pytest
from unittest.mock import MagicMock

from fastapi.security import HTTPAuthorizationCredentials
from app.api.deps.action_token import get_action_token_from_bearer


@pytest.mark.asyncio
async def test_get_action_token_extracts_credentials():
    token = "my_secret_token_123"
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    result = await get_action_token_from_bearer(credentials=credentials)

    assert result == token


@pytest.mark.asyncio
async def test_get_action_token_with_different_token():
    token = "another_token_456"
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    result = await get_action_token_from_bearer(credentials=credentials)

    assert result == token
