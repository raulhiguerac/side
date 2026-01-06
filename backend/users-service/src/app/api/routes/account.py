from typing import Annotated
from sqlmodel import Session

from fastapi import APIRouter, Depends, Response, status

from app.api.deps.db import get_session

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    AccountLogin
)

from app.services.auth_service import create_account_service, create_access_token_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_account_generic_flow(
        payload: RegisterRequest, 
        session: Annotated[Session, Depends(get_session)]
    ):
    account = await create_account_service(session, payload)
    return account

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: AccountLogin, response: Response):
    token = await create_access_token_service(payload)

    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=token.expires_in,
    )

    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/auth/refresh",
        max_age=token.refresh_expires_in,
    )

    return {"message": "ok"}
