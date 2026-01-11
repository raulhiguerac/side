import os
import uuid

from sqlmodel import Session

from fastapi import UploadFile

from app.schemas.auth import Principal
from app.schemas.user import( 
    CurrentUserOut,
    CurrentUserProfileOut,
    CurrentUserPerson, 
    CurrentUserOrganization,
    PhotoUploadOut
)

from app.models.account import AccountType

from app.repositories.account_repository import get_active_account_by_id
from app.repositories.user_repository import get_user_profile_by_account_id, get_company_profile_by_account_id

from app.integrations.cache import CacheClient
from app.integrations.storage import StorageClient

from app.core.exceptions.auth import InvalidTokenException
from app.core.exceptions.user import AccountNotFoundError, AccountDisabledError, ProfileNotFoundError

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))

async def get_current_account(
        session: Session,
        cache: CacheClient, 
        principal: Principal
    ) -> CurrentUserOut:
    try:
        account_id = uuid.UUID(principal.sub)
    except ValueError:
        raise InvalidTokenException("Invalid subject (sub) claim")
    
    cache_key = f"account:{account_id}"

    cached = await cache.get(cache_key)
    if cached:
        return CurrentUserOut.model_validate_json(cached)
     
    current_account = get_active_account_by_id(session,account_id)
    if not current_account:
        raise AccountNotFoundError(account_id=account_id, email=getattr(principal, "email", None))
    if not current_account.is_active:
        raise AccountDisabledError(email=principal.email)
    
    model = CurrentUserOut.model_validate(current_account)
    
    await cache.set(cache_key,model.model_dump_json(),CACHE_TTL_SECONDS)
    
    return model

async def get_current_profile(
        session: Session,
        cache: CacheClient,
        principal: Principal
    ) -> CurrentUserProfileOut:

    account = await get_current_account(session, cache, principal)

    cache_key = f"profile:{account.account_id}"

    cached = await cache.get(cache_key)
    if cached:
        return CurrentUserProfileOut.model_validate_json(cached)

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
    
    out = CurrentUserProfileOut(profile=profile_model)

    await cache.set(cache_key,out.model_dump_json(),600)

    return out

async def upload_current_profile_photo(
        session: Session,
        principal: Principal,
        file: UploadFile,
        bucket: str,
        storage_client: StorageClient,
        base_url: str,
        cache: CacheClient,
    ) -> PhotoUploadOut:

    account = await get_current_account(session, cache, principal)

    if account.account_type == AccountType.person:
        profile_db = get_user_profile_by_account_id(session, account.account_id)
    else:
        profile_db = get_company_profile_by_account_id(session, account.account_id)

    if not profile_db:
        raise ProfileNotFoundError(account_id=account.account_id)

    key = f"accounts/{account.account_id}/profile/photo"
    photo_url = f"{base_url}/{bucket}/{key}"

    storage_client.upload_file(
        fileobj=file.file,
        bucket=bucket,
        key=key,
        extra_args={"ContentType": file.content_type},
    )

    profile_db.photo_url = photo_url
    profile_db.photo_key = key
    session.commit()

    await cache.delete(f"profile:{account.account_id}")

    return PhotoUploadOut(photo_url=profile_db.photo_url)
        
