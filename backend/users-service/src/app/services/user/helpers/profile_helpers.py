import uuid
from typing import Union
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.account import AccountType, UserProfile, CompanyProfile
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.core.exceptions.user import ProfileNotFoundError


ProfileDB = Union[UserProfile, CompanyProfile]


async def get_profile_db(
    *,
    uow: UserUnitOfWork,
    account_id: uuid.UUID,
    account_type: AccountType,
) -> ProfileDB:
    """
    Resolve the profile entity for an account based on its type.
    """

    match account_type:
        case AccountType.person:
            profile = await run_in_threadpool(
                partial(
                    uow.users.get_user_profile_by_id,
                    account_id=account_id,
                )
            )

        case AccountType.organization:
            profile = await run_in_threadpool(
                partial(
                    uow.users.get_company_profile_by_id,
                    account_id=account_id,
                )
            )

        case _:
            profile = None

    if profile is None:
        raise ProfileNotFoundError(account_id=account_id)

    return profile


def account_cache_key(account_id: uuid.UUID) -> str:
    return f"account:{account_id}"


def profile_cache_key(account_id: uuid.UUID) -> str:
    return f"profile:{account_id}"
