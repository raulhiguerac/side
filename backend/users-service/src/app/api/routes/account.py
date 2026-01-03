from typing import Annotated
from sqlmodel import Session

from fastapi import APIRouter, Depends, status

from app.api.deps.db import get_session

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse
)

from app.services.auth_service import create_account_service

router = APIRouter(prefix="/account", tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user_generic_flow(
        payload: RegisterRequest, 
        session: Annotated[Session, Depends(get_session)]
    ):
    user = await create_account_service(session, payload)
    return user
