import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.common import Principal
from app.models.account import Account, AccountActionActor, AccountDeactivationReason
from app.services.user.use_cases.account.deactivate_current_account import DeactivateCurrentAccountUseCase


@pytest.fixture
def principal():
    return Principal(
        sub=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        email_verified=True,
        scope=["users-ms"],
    )


@pytest.fixture
def active_account(principal):
    return Account(
        account_id=principal.sub,
        email=principal.email,
        account_type="person",
        onboarding_step=1,
        is_active=True,
    )


@pytest.fixture
def inactive_account(principal):
    return Account(
        account_id=principal.sub,
        email=principal.email,
        account_type="person",
        onboarding_step=1,
        is_active=False,
    )


@pytest.fixture
def uow():
    return AsyncMock()


@pytest.fixture
def cache_client():
    return AsyncMock()


@pytest.fixture
def uc(uow, cache_client):
    return DeactivateCurrentAccountUseCase(uow=uow, cache_client=cache_client)


# Happy path - deactivate active account
@pytest.mark.asyncio
async def test_deactivate_account_success(uc, principal, uow, cache_client, active_account):
    uow.accounts.get_by_id.return_value = active_account
    uow.commit.return_value = None
    cache_client.delete.return_value = None

    await uc.execute(principal=principal)

    uow.accounts.get_by_id.assert_awaited_once_with(account_id=principal.sub)
    uow.commit.assert_awaited_once()

    # Account should be marked as inactive
    assert active_account.is_active is False
    assert active_account.deactivated_by == AccountActionActor.user
    assert active_account.deactivation_reason == AccountDeactivationReason.user_request
    assert active_account.deactivated_at is not None

    # Cache should be cleared
    assert cache_client.delete.await_count == 2


# Already inactive - idempotent (no-op)
@pytest.mark.asyncio
async def test_deactivate_account_already_inactive(uc, principal, uow, cache_client, inactive_account):
    uow.accounts.get_by_id.return_value = inactive_account

    await uc.execute(principal=principal)

    uow.accounts.get_by_id.assert_awaited_once()
    uow.commit.assert_not_called()
    cache_client.delete.assert_not_called()


# Commit fails - rollback
@pytest.mark.asyncio
async def test_deactivate_account_commit_fails_rollback(uc, principal, uow, cache_client, active_account):
    uow.accounts.get_by_id.return_value = active_account
    uow.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        await uc.execute(principal=principal)

    uow.rollback.assert_awaited_once()
    cache_client.delete.assert_not_called()


# Cache delete fails - silent (best-effort)
@pytest.mark.asyncio
async def test_deactivate_account_cache_delete_fails_silent(uc, principal, uow, cache_client, active_account):
    uow.accounts.get_by_id.return_value = active_account
    uow.commit.return_value = None
    cache_client.delete.side_effect = Exception("Redis error")

    # Should not raise
    await uc.execute(principal=principal)

    uow.commit.assert_awaited_once()
    assert active_account.is_active is False
