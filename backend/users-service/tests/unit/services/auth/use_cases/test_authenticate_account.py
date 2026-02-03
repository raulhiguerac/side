from unittest.mock import AsyncMock
import pytest

from app.services.auth.schemas.login import AccountLogin
from app.services.auth.schemas.tokens import AuthTokens
from app.services.auth.use_cases.authenticate_account import AuthenticateAccountUseCase

from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.services.shared.policies.active_account_policy import AccountActivePolicy

from app.core.exceptions.auth import InvalidCredentialsError

ACCOUNT_LOGIN_DATA = {
    "email": "pepito@micasaenminutos.com",
    "password": "fakepassword",
}


@pytest.fixture
def account_guard():
    return AsyncMock(spec=AccountActivePolicy)


@pytest.fixture
def auth_provider():
    return AsyncMock(spec=AuthenticationProvider)


@pytest.fixture
def uc(account_guard, auth_provider):
    return AuthenticateAccountUseCase(
        account_guard=account_guard,
        auth_provider=auth_provider,
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

# Login happy path
@pytest.mark.asyncio
async def test_authenticate_user_login(uc, account_guard, auth_provider, auth_tokens):
    req = AccountLogin.model_validate(ACCOUNT_LOGIN_DATA)

    account_guard.ensure_active_by_email.return_value = None
    auth_provider.login.return_value = auth_tokens

    result = await uc.login(req=req)

    account_guard.ensure_active_by_email.assert_awaited_once_with(email=req.email)
    auth_provider.login.assert_awaited_once_with(email=req.email, password=req.password)
    assert result == auth_tokens

# Login fail account guard
@pytest.mark.asyncio
async def test_authenticate_user_login_fail_account_guard(uc, account_guard, auth_provider):
    req = AccountLogin.model_validate(ACCOUNT_LOGIN_DATA)
    account_guard.ensure_active_by_email.side_effect = InvalidCredentialsError()

    with pytest.raises(InvalidCredentialsError) as exc_info:
        await uc.login(req=req)

    auth_provider.login.assert_not_awaited()
    account_guard.ensure_active_by_email.assert_awaited_once_with(email=req.email)
    assert exc_info.value.code == "INVALID_CREDENTIALS"

@pytest.mark.asyncio
async def test_get_new_refresh_token(uc, auth_provider, auth_tokens):
    refresh_token_value = "abcd"

    auth_provider.refresh_token.return_value = auth_tokens

    result = await uc.refresh_token(refresh_token=refresh_token_value)

    auth_provider.refresh_token.assert_awaited_once_with(
        refresh_token=refresh_token_value
    )
    assert result == auth_tokens
