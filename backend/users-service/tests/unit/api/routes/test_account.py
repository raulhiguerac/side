import datetime as dt
import uuid
from datetime import timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import Response
from pydantic import TypeAdapter

from app.api.routes.account import (
    change_password,
    confirm_reset_password,
    login,
    logout,
    refresh,
    register_account,
    request_reset_password,
)
from app.models.account import Account
from app.schemas.common import Principal
from app.services.auth.schemas.login import AccountLogin
from app.services.auth.schemas.passwords import ChangePassword, ResetPassword
from app.services.auth.schemas.registration import RegisterRequest
from app.services.auth.schemas.reset import RequestResetPasswordIn
from app.services.auth.schemas.tokens import AuthTokens, RefreshToken


# ----------------------------
# Constants
# ----------------------------

ACCOUNT_ID = uuid.UUID("c42b2c19-efda-4f42-a7e5-1e69190f51e0")

REGISTER_DATA = [
    {
        "first_name": "pepito",
        "last_name": "perez",
        "email": "pepito@micasaenminutos.com",
        "password": "fakepassword",
        "phone": "1234567890",
        "account_type": "person",
    },
    {
        "display_name": "inmobiliaria fake",
        "email": "inmobiliaria@micasaenminutos.com",
        "password": "fakepassword",
        "phone": "1234567890",
        "account_type": "organization",
    },
]

RESET_CONFIRM_TOKEN = (
    "oQeDFF4KHM9EsYgdQY2C9uE18LMq6tGkmVqQgWiKk7wVCHOP1tVU9O0r63vDqRiC"
)

REGISTER_ADAPTER = TypeAdapter(RegisterRequest)


# ----------------------------
# Fixtures
# ----------------------------

@pytest.fixture
def response() -> Response:
    return Response()


@pytest.fixture
def principal() -> Principal:
    return Principal(
        sub=ACCOUNT_ID,
        email="pepito@micasaenminutos.com",
        email_verified=False,
        scope=["users-ms"],
    )


@pytest.fixture
def auth_tokens() -> AuthTokens:
    return AuthTokens(
        access_token="access",
        expires_in=123,
        refresh_token="refresh",
        refresh_expires_in=456,
        token_type="Bearer",
    )


@pytest.fixture
def fixed_now() -> dt.datetime:
    return dt.datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_login_payload() -> AccountLogin:
    return AccountLogin.model_validate(
        {"email": "pepito@micasaenminutos.com", "password": "fakepassword"}
    )


# ----------------------------
# Register
# ----------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("payload_dict", REGISTER_DATA)
async def test_register_calls_uc_and_returns_account(payload_dict, fixed_now):
    payload = REGISTER_ADAPTER.validate_python(payload_dict)

    expected = Account(
        account_id=ACCOUNT_ID,
        email=payload.email,
        account_type=payload.account_type,
        onboarding_step="intent",
        is_active=True,
        deactivated_at=None,
        deactivated_by=None,
        deactivation_reason=None,
        deactivation_note=None,
        reactivated_at=None,
        reactivated_by=None,
        created_at=fixed_now,
        updated_at=fixed_now,
    )

    uc = AsyncMock()
    uc.register = AsyncMock(return_value=expected)

    result = await register_account(payload=payload, uc=uc)

    uc.register.assert_awaited_once_with(req=payload)

    assert result.account_id == expected.account_id
    assert result.email == expected.email
    assert result.account_type == expected.account_type
    assert result.onboarding_step == expected.onboarding_step
    assert result.is_active is True


# ----------------------------
# Login
# ----------------------------

@pytest.mark.asyncio
async def test_login_calls_uc_sets_cookies_and_returns_ok(mocker, response, auth_tokens):
    payload = make_login_payload()

    uc = AsyncMock()
    uc.login = AsyncMock(return_value=auth_tokens)

    set_cookies = mocker.patch(
        "app.api.routes.account.set_auth_cookies",
        autospec=True,
    )

    result = await login(payload=payload, response=response, uc=uc)

    uc.login.assert_awaited_once_with(req=payload)
    set_cookies.assert_called_once_with(response=response, tokens=auth_tokens)
    assert result == {"message": "ok"}


@pytest.mark.asyncio
async def test_login_does_not_set_cookies_if_uc_fails(mocker, response):
    payload = make_login_payload()

    uc = AsyncMock()
    uc.login = AsyncMock(side_effect=Exception("boom"))

    set_cookies = mocker.patch(
        "app.api.routes.account.set_auth_cookies",
        autospec=True,
    )

    with pytest.raises(Exception):
        await login(payload=payload, response=response, uc=uc)

    uc.login.assert_awaited_once_with(req=payload)
    set_cookies.assert_not_called()


# ----------------------------
# Refresh
# ----------------------------

@pytest.mark.asyncio
async def test_refresh_calls_uc_sets_cookies_and_returns_ok(mocker, response, auth_tokens):
    uc = AsyncMock()
    uc.refresh_token = AsyncMock(return_value=auth_tokens)

    set_cookies = mocker.patch(
        "app.api.routes.account.set_auth_cookies",
        autospec=True,
    )

    refresh_obj = RefreshToken(refresh_token="abc")
    result = await refresh(response=response, uc=uc, refresh=refresh_obj)

    uc.refresh_token.assert_awaited_once_with(refresh_token="abc")
    set_cookies.assert_called_once_with(response=response, tokens=auth_tokens)
    assert result == {"message": "ok"}


@pytest.mark.asyncio
async def test_refresh_does_not_set_cookies_if_uc_fails(mocker, response):
    uc = AsyncMock()
    uc.refresh_token = AsyncMock(side_effect=Exception("boom"))

    set_cookies = mocker.patch(
        "app.api.routes.account.set_auth_cookies",
        autospec=True,
    )

    refresh_obj = RefreshToken(refresh_token="abc")

    with pytest.raises(Exception):
        await refresh(response=response, uc=uc, refresh=refresh_obj)

    uc.refresh_token.assert_awaited_once_with(refresh_token="abc")
    set_cookies.assert_not_called()


# ----------------------------
# Change Password
# ----------------------------

@pytest.mark.asyncio
async def test_change_password_calls_uc_deletes_cookies_and_returns_ok(
    mocker, response, principal
):
    payload = ChangePassword(old_password="abc", new_password="abcd")

    uc = AsyncMock()
    uc.change_password = AsyncMock(return_value=None)

    delete_cookies = mocker.patch(
        "app.api.routes.account.delete_auth_cookies",
        autospec=True,
    )

    result = await change_password(
        response=response,
        uc=uc,
        principal=principal,
        payload=payload,
    )

    uc.change_password.assert_awaited_once_with(principal=principal, req=payload)
    delete_cookies.assert_called_once_with(response=response)
    assert result == {"message": "ok"}


@pytest.mark.asyncio
async def test_change_password_does_not_delete_cookies_if_uc_fails(
    mocker, response, principal
):
    payload = ChangePassword(old_password="abc", new_password="abc")

    uc = AsyncMock()
    uc.change_password = AsyncMock(side_effect=Exception("boom"))

    delete_cookies = mocker.patch(
        "app.api.routes.account.delete_auth_cookies",
        autospec=True,
    )

    with pytest.raises(Exception):
        await change_password(response=response, uc=uc, principal=principal, payload=payload)

    delete_cookies.assert_not_called()


# ----------------------------
# Logout
# ----------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("refresh_token_str", ["abc", None])
async def test_logout_calls_uc_deletes_cookies_and_returns_none(
    mocker, response, refresh_token_str
):
    delete_cookies = mocker.patch(
        "app.api.routes.account.delete_auth_cookies",
        autospec=True,
    )

    refresh_obj = (
        RefreshToken(refresh_token=refresh_token_str) if refresh_token_str else None
    )

    uc = AsyncMock()
    uc.logout = AsyncMock(return_value=None)

    result = await logout(response=response, uc=uc, refresh=refresh_obj)

    uc.logout.assert_awaited_once_with(refresh_token=refresh_token_str)
    delete_cookies.assert_called_once_with(response=response)
    assert result is None


# ----------------------------
# Reset Password
# ----------------------------

@pytest.mark.asyncio
async def test_request_reset_password_calls_uc_and_returns_idempotent_message():
    payload = RequestResetPasswordIn(email="pepito@micasaenminutos.com")

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    result = await request_reset_password(payload=payload, uc=uc)

    uc.execute.assert_awaited_once_with(email=payload.email)
    assert result == {
        "message": "If the account exists, a reset email will be sent shortly."
    }


@pytest.mark.asyncio
async def test_confirm_reset_password_calls_uc_and_returns_success_message():
    payload = ResetPassword(new_password="abc", confirm_password="abc")

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    result = await confirm_reset_password(payload=payload, token=RESET_CONFIRM_TOKEN, uc=uc)

    uc.execute.assert_awaited_once_with(token=RESET_CONFIRM_TOKEN, req=payload)
    assert result == {"message": "Password updated successfully."}
