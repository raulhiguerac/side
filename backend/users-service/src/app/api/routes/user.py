from typing import Annotated
from sqlmodel import Session
from redis.asyncio.client import Redis

from fastapi import APIRouter, Depends, status

from app.api.deps.db import get_session
from app.api.deps.redis import get_redis
from app.api.deps.auth import get_current_principal

from app.schemas.user import (
    CurrentUserOut,
    CurrentUserProfileOut,
    PhotoUploadOut
)

from app.schemas.auth import Principal

from app.services.user_service import get_current_account, get_current_profile

router = APIRouter(prefix="/users", tags=["profile"])

@router.get("/me", response_model=CurrentUserOut, status_code=status.HTTP_200_OK)
async def get_current_user(
        session: Annotated[Session, Depends(get_session)],
        redis: Annotated[Redis, Depends(get_redis)],
        principal: Annotated[Principal, Depends(get_current_principal)]
    ):
    user = await get_current_account(session, redis, principal)
    return user

@router.get("/me/profile", response_model=CurrentUserProfileOut, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
        session: Annotated[Session, Depends(get_session)],
        redis: Annotated[Redis, Depends(get_redis)],
        principal: Annotated[Principal, Depends(get_current_principal)]
    ):
    user = await get_current_profile(session, redis, principal)
    return user

@router.post("/me/profile/photo", response_model=PhotoUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_user_photo(
        session: Annotated[Session, Depends(get_session)],
        principal: Annotated[Principal, Depends(get_current_principal)]
    ):
    user_photo = await upload_current_profile_photo(session, principal)
    return user_photo