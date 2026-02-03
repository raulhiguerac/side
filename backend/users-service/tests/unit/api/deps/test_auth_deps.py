import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Request

from app.api.deps.auth import (
    get_refresh_token_from_cookie,
    get_refresh_token_from_cookie_optional,
)
from app.core.exceptions.auth import MissingCookieException
from app.services.auth.schemas.tokens import RefreshToken


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.cookies = {}
    request.state = MagicMock()
    return request


# get_refresh_token_from_cookie
@pytest.mark.asyncio
async def test_get_refresh_token_from_cookie_success(mock_request):
    mock_request.cookies = {"refresh_token": "my_refresh_token"}

    result = await get_refresh_token_from_cookie(mock_request)

    assert isinstance(result, RefreshToken)
    assert result.refresh_token == "my_refresh_token"


@pytest.mark.asyncio
async def test_get_refresh_token_from_cookie_missing(mock_request):
    mock_request.cookies = {}

    with pytest.raises(MissingCookieException):
        await get_refresh_token_from_cookie(mock_request)


# get_refresh_token_from_cookie_optional
@pytest.mark.asyncio
async def test_get_refresh_token_optional_success(mock_request):
    mock_request.cookies = {"refresh_token": "my_refresh_token"}

    result = await get_refresh_token_from_cookie_optional(mock_request)

    assert isinstance(result, RefreshToken)
    assert result.refresh_token == "my_refresh_token"


@pytest.mark.asyncio
async def test_get_refresh_token_optional_missing(mock_request):
    mock_request.cookies = {}

    result = await get_refresh_token_from_cookie_optional(mock_request)

    assert result is None
