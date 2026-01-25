from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.deps.auth import (
    get_refresh_token_from_cookie, 
    get_refresh_token_from_cookie_optional, 
    get_current_principal
)
from app.api.deps.auth_use_cases import (
    get_authenticate_account_uc,
    get_register_account_uc,
    get_change_password_uc,
    get_logout_account_uc
)
from app.api.http.cookies import set_auth_cookies, delete_auth_cookies

from app.schemas.common import Principal
from app.services.auth.schemas.registration import RegisterRequest, RegisterResponse
from app.services.auth.schemas.login import AccountLogin
from app.services.auth.schemas.tokens import RefreshToken
from app.services.auth.schemas.passwords import ChangePassword

from app.services.auth.use_cases.authenticate_account import (
    AuthenticateAccountUseCase,
)
from app.services.auth.use_cases.register_account import (
    RegisterAccountUseCase,
)
from app.services.auth.use_cases.change_password import (
    ChangeAccountPasswordUseCase,
)
from app.services.auth.use_cases.logout import (
    LogoutUseCase,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_account(
    payload: RegisterRequest,
    uc: Annotated[RegisterAccountUseCase, Depends(get_register_account_uc)],
):
    """
    Register a new account (DB + Identity Provider).
    """
    return await uc.register(req=payload)

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    payload: AccountLogin,
    response: Response,
    uc: Annotated[AuthenticateAccountUseCase, Depends(get_authenticate_account_uc)],
):
    """
    Authenticate an account and set auth cookies.
    """
    tokens = await uc.login(req=payload)
    set_auth_cookies(response=response, tokens=tokens)

    return {"message": "ok"}

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    uc: Annotated[AuthenticateAccountUseCase, Depends(get_authenticate_account_uc)],
    refresh: Annotated[RefreshToken, Depends(get_refresh_token_from_cookie)],
):
    """
    Refresh access token using refresh token from cookies.
    """
    tokens = await uc.refresh_token(refresh_token=refresh.refresh_token)
    set_auth_cookies(response=response, tokens=tokens)

    return {"message": "ok"}


@router.post("/change_password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: ChangePassword,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[ChangeAccountPasswordUseCase, Depends(get_change_password_uc)],
    response: Response,
):
    """
    Change the current user's password and invalidate the session.
    """
    await uc.change_password(principal=principal, req=payload)

    delete_auth_cookies(response=response)

    return {"message": "ok"}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh: Annotated[RefreshToken | None, Depends(get_refresh_token_from_cookie_optional)],
    uc: Annotated[LogoutUseCase, Depends(get_logout_account_uc)],
    response: Response,
):
    """Logout the current user and invalidate the session."""

    delete_auth_cookies(response=response)
    await uc.logout(
        refresh_token=refresh.refresh_token if refresh else None
    )
