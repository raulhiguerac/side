from typing import Annotated
from sqlmodel import Session

from fastapi import APIRouter, Depends, status

from app.api.deps.db import get_session

from app.schemas.user import (
    CurrentUserOut
)

from app.services.auth_service import create_account_service

router = APIRouter(prefix="/users", tags=["profile"])

@router.get("/me", response_model=CurrentUserOut, status_code=status.HTTP_200_OK)
async def get_current_user(
        session: Annotated[Session, Depends(get_session)]
    ):
    user = await get_current_user_service(session, payload)
    return user
