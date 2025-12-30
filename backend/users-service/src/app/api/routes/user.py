from typing import Annotated
from sqlmodel import Session

from fastapi import APIRouter, Depends, status

from app.api.deps.db import get_session

from app.schemas.user import (
    UserGeneric,
    UserOut
)

from app.services.user_service import create_user_service

router = APIRouter(prefix="/register", tags=["auth"])

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user_generic_flow(
        payload: UserGeneric, 
        session: Annotated[Session, Depends(get_session)]
    ):
    user = await create_user_service(session, payload)
    return user
