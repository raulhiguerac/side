from typing import Annotated
from sqlmodel import Session
from fastapi import APIRouter, Depends, status, UploadFile, File

from app.api.deps.db import get_session
from app.api.deps.cache import get_cache
from app.api.deps.auth import get_current_principal
from app.api.deps.storage import get_storage, get_profile_photos_bucket,get_public_base_url
from app.api.deps.upload_validation import validate_profile_photo_upload
from app.integrations.cache import CacheClient
from app.integrations.storage import StorageClient
from app.schemas.user import CurrentUserOut, CurrentUserProfileOut, PhotoUploadOut
from app.schemas.auth import Principal
from app.services.user_service import get_current_account, get_current_profile, upload_current_profile_photo

router = APIRouter(prefix="/users", tags=["profile"])

@router.get("/me", response_model=CurrentUserOut, status_code=status.HTTP_200_OK)
async def get_current_user(
        session: Annotated[Session, Depends(get_session)],
        cache: Annotated[CacheClient, Depends(get_cache)],
        principal: Annotated[Principal, Depends(get_current_principal)]
    ):
    user = await get_current_account(session, cache, principal)
    return user

@router.get("/me/profile", response_model=CurrentUserProfileOut, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
        session: Annotated[Session, Depends(get_session)],
        cache: Annotated[CacheClient, Depends(get_cache)],
        principal: Annotated[Principal, Depends(get_current_principal)]
    ):
    user = await get_current_profile(session, cache, principal)
    return user

@router.post("/me/profile/photo", response_model=PhotoUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_user_photo(
        session: Annotated[Session, Depends(get_session)],
        principal: Annotated[Principal, Depends(get_current_principal)],
        file: Annotated[UploadFile, File(...)],
        _: Annotated[None, Depends(validate_profile_photo_upload)],
        storage_client: Annotated[StorageClient, Depends(get_storage)],
        bucket: Annotated[str, Depends(get_profile_photos_bucket)],
        base_url: Annotated[str, Depends(get_public_base_url)],
        cache: Annotated[CacheClient, Depends(get_cache)],
    ):
    user_photo = await upload_current_profile_photo(
        session=session,
        principal=principal,
        file=file,
        bucket=bucket,
        storage_client=storage_client,
        base_url=base_url,
        cache=cache
    )
    return user_photo