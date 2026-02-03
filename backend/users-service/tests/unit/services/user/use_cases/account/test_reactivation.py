import uuid
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from app.models.account import Account, AccountActionActor, AccountType
from app.services.user.use_cases.account.request_account_reactivation import RequestReactivationUseCase
from app.services.user.use_cases.account.reactivate_current_account import ConfirmReactivationUseCase
from app.core.exceptions.account import AccountNotFoundError
from app.core.exceptions.auth import TokenInvalidOrExpiredError


# =============================================================================
# RequestReactivationUseCase
# =============================================================================


@pytest.fixture
def uow():
    return AsyncMock()


@pytest.fixture
def cache_client():
    return AsyncMock()


@pytest.fixture
def profile_service():
    return AsyncMock()


@pytest.fixture
def reactivation_mailer():
    return AsyncMock()


@pytest.fixture
def request_uc(uow, cache_client, profile_service, reactivation_mailer):
    return RequestReactivationUseCase(
        uow=uow,
        cache_client=cache_client,
        profile_service=profile_service,
        reactivation_mailer=reactivation_mailer,
    )


@pytest.fixture
def eligible_account():
    """Account that was deactivated by user - eligible for reactivation"""
    return Account(
        account_id=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=False,
        deactivated_at=datetime.utcnow(),
        deactivated_by=AccountActionActor.user,
    )


@pytest.fixture
def ineligible_account_active():
    """Active account - not eligible"""
    return Account(
        account_id=uuid.uuid4(),
        email="active@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=True,
    )


@pytest.fixture
def ineligible_account_admin_deactivated():
    """Deactivated by admin - not eligible for self-reactivation"""
    return Account(
        account_id=uuid.uuid4(),
        email="admin_deactivated@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=False,
        deactivated_at=datetime.utcnow(),
        deactivated_by=AccountActionActor.admin,
    )


@pytest.fixture
def mock_profile():
    profile = MagicMock()
    profile.account_type = AccountType.person
    profile.first_name = "Pepito"
    return profile


@pytest.fixture
def mock_profile_out(mock_profile):
    out = MagicMock()
    out.profile = mock_profile
    return out


# Happy path - eligible account
@pytest.mark.asyncio
async def test_request_reactivation_success(
    request_uc, uow, cache_client, profile_service, reactivation_mailer, eligible_account, mock_profile_out
):
    uow.accounts.get_by_email.return_value = eligible_account
    profile_service.get_profile.return_value = mock_profile_out
    cache_client.set_json.return_value = None
    reactivation_mailer.send_reactivation_email.return_value = None

    await request_uc.execute(email=eligible_account.email)

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_awaited_once()
    reactivation_mailer.send_reactivation_email.assert_awaited_once()


# Account not found - idempotent (silent)
@pytest.mark.asyncio
async def test_request_reactivation_account_not_found(
    request_uc, uow, cache_client, reactivation_mailer
):
    uow.accounts.get_by_email.side_effect = AccountNotFoundError(email="notfound@x.com")

    await request_uc.execute(email="notfound@x.com")

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_not_called()
    reactivation_mailer.send_reactivation_email.assert_not_called()


# Account is active - not eligible (silent)
@pytest.mark.asyncio
async def test_request_reactivation_account_active(
    request_uc, uow, cache_client, reactivation_mailer, ineligible_account_active
):
    uow.accounts.get_by_email.return_value = ineligible_account_active

    await request_uc.execute(email=ineligible_account_active.email)

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_not_called()
    reactivation_mailer.send_reactivation_email.assert_not_called()


# Account deactivated by admin - not eligible (silent)
@pytest.mark.asyncio
async def test_request_reactivation_admin_deactivated(
    request_uc, uow, cache_client, reactivation_mailer, ineligible_account_admin_deactivated
):
    uow.accounts.get_by_email.return_value = ineligible_account_admin_deactivated

    await request_uc.execute(email=ineligible_account_admin_deactivated.email)

    uow.accounts.get_by_email.assert_awaited_once()
    cache_client.set_json.assert_not_called()
    reactivation_mailer.send_reactivation_email.assert_not_called()


# =============================================================================
# ConfirmReactivationUseCase
# =============================================================================


@pytest.fixture
def confirm_uc(uow, cache_client):
    return ConfirmReactivationUseCase(uow=uow, cache_client=cache_client)


@pytest.fixture
def inactive_account():
    return Account(
        account_id=uuid.uuid4(),
        email="inactive@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=False,
        deactivated_at=datetime.utcnow(),
        deactivated_by=AccountActionActor.user,
    )


@pytest.fixture
def active_account():
    return Account(
        account_id=uuid.uuid4(),
        email="active@micasaenminutos.com",
        account_type="person",
        onboarding_step=1,
        is_active=True,
    )


# Happy path
@pytest.mark.asyncio
async def test_confirm_reactivation_success(confirm_uc, uow, cache_client, inactive_account):
    token = "valid_token"

    cache_client.getdel_json.return_value = {"account_id": str(inactive_account.account_id)}
    uow.accounts.get_by_id.return_value = inactive_account
    uow.commit.return_value = None

    await confirm_uc.execute(token=token)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_awaited_once()
    uow.commit.assert_awaited_once()

    # Account should be reactivated
    assert inactive_account.is_active is True
    assert inactive_account.deactivated_at is None
    assert inactive_account.deactivated_by is None
    assert inactive_account.reactivated_at is not None
    assert inactive_account.reactivated_by == AccountActionActor.user


# Token invalid/expired
@pytest.mark.asyncio
async def test_confirm_reactivation_token_invalid(confirm_uc, cache_client, uow):
    token = "invalid_token"
    cache_client.getdel_json.return_value = None

    with pytest.raises(TokenInvalidOrExpiredError):
        await confirm_uc.execute(token=token)

    cache_client.getdel_json.assert_awaited_once()
    uow.accounts.get_by_id.assert_not_called()


# Account not found
@pytest.mark.asyncio
async def test_confirm_reactivation_account_not_found(confirm_uc, cache_client, uow):
    token = "valid_token"
    account_id = uuid.uuid4()

    cache_client.getdel_json.return_value = {"account_id": str(account_id)}
    uow.accounts.get_by_id.return_value = None

    with pytest.raises(TokenInvalidOrExpiredError):
        await confirm_uc.execute(token=token)


# Already active - idempotent (no-op)
@pytest.mark.asyncio
async def test_confirm_reactivation_already_active(confirm_uc, uow, cache_client, active_account):
    token = "valid_token"

    cache_client.getdel_json.return_value = {"account_id": str(active_account.account_id)}
    uow.accounts.get_by_id.return_value = active_account

    await confirm_uc.execute(token=token)

    uow.commit.assert_not_called()  # No changes needed


# Commit fails - rollback
@pytest.mark.asyncio
async def test_confirm_reactivation_commit_fails(confirm_uc, uow, cache_client, inactive_account):
    token = "valid_token"

    cache_client.getdel_json.return_value = {"account_id": str(inactive_account.account_id)}
    uow.accounts.get_by_id.return_value = inactive_account
    uow.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        await confirm_uc.execute(token=token)

    uow.rollback.assert_awaited_once()
