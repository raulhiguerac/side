import os
import uuid

from sqlmodel import Session

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services.user.helpers.profile_helpers import get_profile_db, account_cache_key, profile_cache_key
from app.services.user.mapper import map_profile_db_to_schema

from app.schemas.auth import Principal
from app.schemas.user import( 
    CurrentUserOut,
    CurrentUserProfileOut,
    PhotoUploadOut,
    UpdateRequest
)

from app.repositories.account_repository import get_account_by_id

from app.integrations.cache.redis.cache import CacheClient
from app.integrations.storage.minio.storage import StorageClient

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.core.exceptions.auth import InvalidTokenException
from app.core.exceptions.user import AccountNotFoundError, AccountDisabledError

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))
PROFILE_CACHE_TTL_SECONDS = int(os.getenv("PROFILE_CACHE_TTL_SECONDS", "600"))

async def get_current_account(
        session: Session,
        cache: CacheClient, 
        principal: Principal
    ) -> CurrentUserOut:
    try:
        account_id = uuid.UUID(principal.sub)
    except ValueError:
        raise InvalidTokenException("Invalid subject (sub) claim")
    
    cache_key = account_cache_key(account_id)

    cached = await cache.get(cache_key)
    if cached:
        return CurrentUserOut.model_validate_json(cached)
     
    current_account = await run_in_threadpool(get_account_by_id, session, account_id)
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

    cache_key = profile_cache_key(account.account_id)

    cached = await cache.get(cache_key)
    if cached:
        return CurrentUserProfileOut.model_validate_json(cached)
    
    profile_db = await get_profile_db(session, account.account_id, account.account_type)

    profile_model = map_profile_db_to_schema(account.account_type, profile_db)
    
    out = CurrentUserProfileOut(profile=profile_model)

    await cache.set(cache_key,out.model_dump_json(),PROFILE_CACHE_TTL_SECONDS)

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

    profile_db = await get_profile_db(session, account.account_id, account.account_type)

    key = f"accounts/{account.account_id}/profile/photo"
    photo_url = f"{base_url}/{bucket}/{key}"

    await run_in_threadpool(
        storage_client.upload_file,
        fileobj=file.file,
        bucket=bucket,
        key=key,
        extra_args={"ContentType": file.content_type},
    )

    profile_db.photo_url = photo_url
    profile_db.photo_key = key
    session.commit()

    await cache.delete(profile_cache_key(account.account_id))

    return PhotoUploadOut(photo_url=profile_db.photo_url)

async def update_profile(
        session: Session,
        cache: CacheClient,
        principal: Principal,
        updated_data: UpdateRequest
    ) -> CurrentUserProfileOut:

    account = await get_current_account(session, cache, principal)

    profile_db = await get_profile_db(session, account.account_id, account.account_type)

    data = updated_data.model_dump(exclude_unset=True, exclude={"account_type"})
    for field, value in data.items():
        setattr(profile_db, field, value)
 
    try:
        session.commit()
        session.refresh(profile_db)
    except IntegrityError as e:
        session.rollback()
        raise
    except SQLAlchemyError as e:
        session.rollback()
        raise

    await cache.delete(profile_cache_key(account.account_id))
    out = CurrentUserProfileOut(profile=map_profile_db_to_schema(account.account_type, profile_db))
    await cache.set(profile_cache_key(account.account_id),out.model_dump_json(),PROFILE_CACHE_TTL_SECONDS)

    return out
    

        
