import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.user.use_cases.account.resolve_accounts_bulk import ResolveAccountsBulkUseCase


@pytest.fixture
def account_reader():
    return AsyncMock()


@pytest.fixture
def uc(account_reader):
    return ResolveAccountsBulkUseCase(account_reader=account_reader)


@pytest.mark.asyncio
async def test_resolves_emails_to_account_id_pairs(uc, account_reader):
    account_id = uuid.uuid4()
    account_reader.get_accounts_bulk.return_value = [(account_id, "a@test.com")]

    result = await uc.execute(emails=["a@test.com"])

    assert result == [(account_id, "a@test.com")]
    account_reader.get_accounts_bulk.assert_awaited_once_with(emails=["a@test.com"])


@pytest.mark.asyncio
async def test_unknown_or_inactive_emails_are_simply_absent(uc, account_reader):
    """Callers rely on this: a missing email means "no active account", which
    downstream turns into a per-row error rather than a wrong owner."""
    known = uuid.uuid4()
    account_reader.get_accounts_bulk.return_value = [(known, "a@test.com")]

    result = await uc.execute(emails=["a@test.com", "ghost@test.com"])

    assert [email for _, email in result] == ["a@test.com"]


@pytest.mark.asyncio
async def test_empty_input_is_passed_through(uc, account_reader):
    account_reader.get_accounts_bulk.return_value = []

    assert await uc.execute(emails=[]) == []
