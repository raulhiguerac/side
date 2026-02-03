import uuid
import pytest
from unittest.mock import AsyncMock

from app.schemas.common import Principal
from app.services.user.schemas.current import CurrentUserOut
from app.services.user.use_cases.account.get_current_account import GetCurrentAccountUseCase


@pytest.fixture
def principal():
    return Principal(
        sub=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        email_verified=True,
        scope=["users-ms"],
    )


@pytest.fixture
def account_reader():
    return AsyncMock()


@pytest.fixture
def uc(account_reader):
    return GetCurrentAccountUseCase(account_reader=account_reader)


# Happy path
@pytest.mark.asyncio
async def test_get_current_account_success(uc, principal, account_reader):
    expected = CurrentUserOut(
        account_id=principal.sub,
        email=principal.email,
        account_type="person",
        onboarding_step="intent",
        is_active=True,
    )
    account_reader.get_active.return_value = expected

    result = await uc.execute(principal=principal)

    account_reader.get_active.assert_awaited_once_with(account_id=principal.sub)
    assert result == expected
