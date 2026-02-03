import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.account import AccountType, UserProfile, CompanyProfile
from app.services.user.helpers.profile_reader import get_profile_db
from app.core.exceptions.user import ProfileNotFoundError


@pytest.fixture
def uow():
    return MagicMock()


@pytest.fixture
def user_profile():
    return UserProfile(
        account_id=uuid.uuid4(),
        first_name="Pepito",
        last_name="Perez",
    )


@pytest.fixture
def company_profile():
    return CompanyProfile(
        account_id=uuid.uuid4(),
        display_name="Test Company",
    )


# Person profile
@pytest.mark.asyncio
async def test_get_profile_db_person(uow, user_profile):
    account_id = user_profile.account_id
    uow.users.get_user_profile_by_id.return_value = user_profile

    result = await get_profile_db(
        uow=uow,
        account_id=account_id,
        account_type=AccountType.person,
    )

    assert result == user_profile
    uow.users.get_user_profile_by_id.assert_called_once_with(account_id=account_id)


# Organization profile
@pytest.mark.asyncio
async def test_get_profile_db_organization(uow, company_profile):
    account_id = company_profile.account_id
    uow.users.get_company_profile_by_id.return_value = company_profile

    result = await get_profile_db(
        uow=uow,
        account_id=account_id,
        account_type=AccountType.organization,
    )

    assert result == company_profile
    uow.users.get_company_profile_by_id.assert_called_once_with(account_id=account_id)


# Profile not found
@pytest.mark.asyncio
async def test_get_profile_db_not_found(uow):
    account_id = uuid.uuid4()
    uow.users.get_user_profile_by_id.return_value = None

    with pytest.raises(ProfileNotFoundError):
        await get_profile_db(
            uow=uow,
            account_id=account_id,
            account_type=AccountType.person,
        )
