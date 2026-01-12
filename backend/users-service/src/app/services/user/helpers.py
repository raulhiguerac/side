import uuid
from sqlmodel import Session

from fastapi.concurrency import run_in_threadpool

from app.models.account import AccountType

from app.repositories.user_repository import get_user_profile_by_account_id, get_company_profile_by_account_id

from app.core.exceptions.user import ProfileNotFoundError

async def get_profile_db(session: Session, account_id: uuid.UUID, account_type: AccountType):
    match account_type:
        case AccountType.person:
            profile_db = await run_in_threadpool(
                get_user_profile_by_account_id,
                session,
                account_id
            )
        case AccountType.organization:
            profile_db = await run_in_threadpool(
                get_company_profile_by_account_id,
                session,
                account_id
            )
        case _:
            profile_db = None

    if not profile_db:
        raise ProfileNotFoundError(account_id=account_id)

    return profile_db

def account_cache_key(account_id: uuid.UUID) -> str:
    return f"account:{account_id}"

def profile_cache_key(account_id: uuid.UUID) -> str:
    return f"profile:{account_id}"