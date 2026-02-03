import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.common import Principal
from app.services.auth.schemas.passwords import ChangePassword
from app.services.auth.use_cases.change_password import ChangeAccountPasswordUseCase
from app.core.exceptions.auth import SamePasswordNotAllowedError


@pytest.fixture
def principal():
    return Principal(
        sub=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        email_verified=True,
        scope=["users-ms"],
    )


@pytest.fixture
def idp():
    return AsyncMock()


@pytest.fixture
def auth_provider():
    return AsyncMock()


@pytest.fixture
def account_policy():
    return AsyncMock()


@pytest.fixture
def uc(idp, auth_provider, account_policy):
    return ChangeAccountPasswordUseCase(
        idp=idp,
        auth_provider=auth_provider,
        account_policy=account_policy,
    )


# Happy path
@pytest.mark.asyncio
async def test_change_password_success(uc, principal, idp, auth_provider, account_policy):
    req = ChangePassword(old_password="oldpass", new_password="newpass")

    account_policy.ensure_active_by_id.return_value = None
    auth_provider.login.return_value = None
    idp.reset_password.return_value = None

    await uc.change_password(principal=principal, req=req)

    account_policy.ensure_active_by_id.assert_awaited_once_with(account_id=principal.sub)
    auth_provider.login.assert_awaited_once_with(email=principal.email, password=req.old_password)
    idp.reset_password.assert_awaited_once_with(account_id=principal.sub, new_password=req.new_password)


# Same password not allowed
@pytest.mark.asyncio
async def test_change_password_fails_if_same_password(uc, principal, idp, auth_provider, account_policy):
    req = ChangePassword(old_password="samepass", new_password="samepass")

    with pytest.raises(SamePasswordNotAllowedError):
        await uc.change_password(principal=principal, req=req)

    # Nothing should be called
    account_policy.ensure_active_by_id.assert_not_called()
    auth_provider.login.assert_not_called()
    idp.reset_password.assert_not_called()
