import os
import json
import uuid

from sqlmodel import Session
from redis.asyncio.client import Redis

from app.schemas.auth import Principal
from app.schemas.user import( 
    CurrentUserOut,
    CurrentUserProfileOut,
    CurrentUserPerson, 
    CurrentUserOrganization
)

from app.models.account import AccountType

from app.repositories.account_repository import get_active_account_by_id
from app.repositories.user_repository import get_user_profile_by_account_id, get_company_profile_by_account_id

from redis.exceptions import RedisError

from app.core.exceptions.auth import InvalidTokenException
from app.core.exceptions.user import AccountNotFoundError, AccountDisabledError, ProfileNotFoundError

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))

async def get_current_account(
        session: Session,
        redis: Redis, 
        principal: Principal
    ) -> CurrentUserOut:
    try:
        account_id = uuid.UUID(principal.sub)
    except ValueError:
        raise InvalidTokenException("Invalid subject (sub) claim")
    
    cache_key = f"account:{account_id}"

    try:
        cached = await redis.get(cache_key)
        if cached:
            return CurrentUserOut.model_validate_json(cached)
    except (RedisError, ValueError):
        pass
     
    current_account = get_active_account_by_id(session,account_id)
    if not current_account:
        raise AccountNotFoundError(account_id=account_id, email=getattr(principal, "email", None))
    if not current_account.is_active:
        raise AccountDisabledError(email=principal.email)
    
    model = CurrentUserOut.model_validate(current_account)
    
    try:
        await redis.set(
            cache_key,
            model.model_dump_json(),
            ex=CACHE_TTL_SECONDS,
        )
    except RedisError:
        pass
    
    return model

async def get_current_profile(
        session: Session,
        redis: Redis, 
        principal: Principal
    ) -> CurrentUserProfileOut:
    account = await get_current_account(session, redis, principal)

    if account.account_type == AccountType.person:
        profile_db = get_user_profile_by_account_id(session, account.account_id)
        if not profile_db:
            raise ProfileNotFoundError(account_id=account.account_id)

        profile_model = CurrentUserPerson(
            first_name=profile_db.first_name,
            last_name=profile_db.last_name,
            phone=profile_db.phone,
            photo_url=profile_db.photo_url,
            description=profile_db.description,
            account_type="person",
        )

    else:
        profile_db = get_company_profile_by_account_id(session, account.account_id)
        if not profile_db:
            raise ProfileNotFoundError(account_id=account.account_id)

        profile_model = CurrentUserOrganization(
            display_name=profile_db.display_name,
            phone=profile_db.phone,
            photo_url=profile_db.photo_url,
            description=profile_db.description,
            account_type="organization",
        )

    return CurrentUserProfileOut(profile=profile_model)