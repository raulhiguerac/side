import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.account import Account
from app.services.auth.use_cases.request_reset_password import RequestResetPasswordUseCase
from app.services.auth.use_cases.confirm_reset_password import ConfirmResetPasswordUseCase
from app.services.auth.schemas.passwords import ResetPassword
from app.core.exceptions.auth import TokenInvalidOrExpiredError, PasswordsDoNotMatchError


# =============================================================================
# RequestResetPasswordUseCase
# =============================================================================


@pytest.fixture
def uow():
    return AsyncMock()


@pytest.fixture
def cache_client():
    return AsyncMock()


@pytest.fixture
def reset_password_mailer():
    return AsyncMock()


@pytest.fixture
def request_reset_uc(uow, cache_client, reset_password_mailer):
    return RequestResetPasswordUseCase(
        uow=uow,
        cache_client=cache_client,
        reset_password_mailer=reset_password_mailer,
    )


@pytest.fixture
def active_account():
    return Account(
        account_id=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=True,
    )


@pytest.fixture
def inactive_account():
    return Account(
        account_id=uuid.uuid4(),
        email="inactive@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=False,
    )


# Happy path - account exists and is active
@pytest.mark.asyncio
async def test_request_reset_password_success(request_reset_uc, uow, cache_client, reset_password_mailer, active_account):
    uow.accounts.get_by_email.return_value = active_account
    uow.email_recipients.get_display_name_by_account_id.return_value = "Pepito"
    cache_client.set_json.return_value = None
    reset_password_mailer.send_reset_password_email.return_value = None

    await request_reset_uc.execute(email=active_account.email)

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_awaited_once()
    reset_password_mailer.send_reset_password_email.assert_awaited_once()


# Account does not exist (idempotent - no error)
@pytest.mark.asyncio
async def test_request_reset_password_account_not_found(request_reset_uc, uow, cache_client, reset_password_mailer):
    uow.accounts.get_by_email.return_value = None

    await request_reset_uc.execute(email="nonexistent@micasaenminutos.com")

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_not_called()
    reset_password_mailer.send_reset_password_email.assert_not_called()


# Account is inactive (idempotent - no error)
@pytest.mark.asyncio
async def test_request_reset_password_account_inactive(request_reset_uc, uow, cache_client, reset_password_mailer, inactive_account):
    uow.accounts.get_by_email.return_value = inactive_account

    await request_reset_uc.execute(email=inactive_account.email)

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_not_called()
    reset_password_mailer.send_reset_password_email.assert_not_called()


# =============================================================================
# ConfirmResetPasswordUseCase
# =============================================================================


@pytest.fixture
def idp():
    return AsyncMock()


@pytest.fixture
def confirm_reset_uc(idp, uow, cache_client):
    return ConfirmResetPasswordUseCase(
        idp=idp,
        uow=uow,
        cache_client=cache_client,
    )


# Happy path
@pytest.mark.asyncio
async def test_confirm_reset_password_success(confirm_reset_uc, uow, cache_client, idp, active_account):
    req = ResetPassword(new_password="newpass123", confirm_password="newpass123")
    token = "valid_token"

    cache_client.getdel_json.return_value = {"account_id": str(active_account.account_id)}
    uow.accounts.get_by_id.return_value = active_account
    idp.reset_password.return_value = None

    await confirm_reset_uc.execute(token=token, req=req)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_awaited_once_with(account_id=active_account.account_id)
    idp.reset_password.assert_awaited_once_with(
        account_id=active_account.account_id,
        new_password=req.new_password,
    )


# Passwords do not match
@pytest.mark.asyncio
async def test_confirm_reset_password_passwords_mismatch(confirm_reset_uc, cache_client, uow, idp):
    req = ResetPassword(new_password="newpass123", confirm_password="different")
    token = "valid_token"

    with pytest.raises(PasswordsDoNotMatchError):
        await confirm_reset_uc.execute(token=token, req=req)

    cache_client.getdel_json.assert_not_called()
    uow.accounts.get_by_id.assert_not_called()
    idp.reset_password.assert_not_called()


# Token invalid or expired (not in cache)
@pytest.mark.asyncio
async def test_confirm_reset_password_token_invalid(confirm_reset_uc, cache_client, uow, idp):
    req = ResetPassword(new_password="newpass123", confirm_password="newpass123")
    token = "invalid_token"

    cache_client.getdel_json.return_value = None

    with pytest.raises(TokenInvalidOrExpiredError):
        await confirm_reset_uc.execute(token=token, req=req)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_not_called()
    idp.reset_password.assert_not_called()


# Account not found after token consumed
@pytest.mark.asyncio
async def test_confirm_reset_password_account_not_found(confirm_reset_uc, cache_client, uow, idp):
    req = ResetPassword(new_password="newpass123", confirm_password="newpass123")
    token = "valid_token"
    account_id = uuid.uuid4()

    cache_client.getdel_json.return_value = {"account_id": str(account_id)}
    uow.accounts.get_by_id.return_value = None

    with pytest.raises(TokenInvalidOrExpiredError):
        await confirm_reset_uc.execute(token=token, req=req)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_awaited_once()
    idp.reset_password.assert_not_called()


# Account inactive - silently returns (no error, no password reset)
@pytest.mark.asyncio
async def test_confirm_reset_password_account_inactive(confirm_reset_uc, cache_client, uow, idp, inactive_account):
    req = ResetPassword(new_password="newpass123", confirm_password="newpass123")
    token = "valid_token"

    cache_client.getdel_json.return_value = {"account_id": str(inactive_account.account_id)}
    uow.accounts.get_by_id.return_value = inactive_account

    # Should not raise, just return silently
    await confirm_reset_uc.execute(token=token, req=req)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_awaited_once()
    idp.reset_password.assert_not_called()  # Password NOT reset for inactive account
