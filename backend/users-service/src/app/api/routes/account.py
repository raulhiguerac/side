from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

# Dependencies
from app.api.deps.action_token import get_action_token_from_bearer
from app.api.deps.auth import (
    get_current_principal,
    get_refresh_token_from_cookie,
    get_refresh_token_from_cookie_optional,
)
from app.api.deps.auth_use_cases import (
    get_authenticate_account_uc,
    get_change_password_uc,
    get_confirm_reset_password_uc,
    get_logout_account_uc,
    get_register_account_uc,
    get_reset_password_uc,
)
from app.api.http.cookies import delete_auth_cookies, set_auth_cookies

# Schemas
from app.schemas.common import Principal
from app.services.auth.schemas.login import AccountLogin
from app.services.auth.schemas.passwords import ChangePassword, ResetPassword
from app.services.auth.schemas.registration import RegisterRequest, RegisterResponse
from app.services.auth.schemas.reset import RequestResetPasswordIn
from app.services.auth.schemas.tokens import RefreshToken

# Use cases
from app.services.auth.use_cases.authenticate_account import AuthenticateAccountUseCase
from app.services.auth.use_cases.change_password import ChangeAccountPasswordUseCase
from app.services.auth.use_cases.confirm_reset_password import ConfirmResetPasswordUseCase
from app.services.auth.use_cases.logout import LogoutUseCase
from app.services.auth.use_cases.register_account import RegisterAccountUseCase
from app.services.auth.use_cases.request_reset_password import RequestResetPasswordUseCase

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


@router.post("/change-password", status_code=status.HTTP_200_OK)
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

@router.post(
    "/reset-password/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Sends a password reset email if the account exists.",
)
async def request_reset_password(
    payload: RequestResetPasswordIn,
    uc: Annotated[
        RequestResetPasswordUseCase,
        Depends(get_reset_password_uc),
    ],
) -> dict[str, str]:
    await uc.execute(email=payload.email)

    return {
        "message": (
            "If the account exists, a reset email will be sent shortly."
        )
    }

@router.post(
    "/reset-password/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Sets a new password using a one-time reset token.",
)
async def confirm_reset_password(
    payload: ResetPassword,
    token: Annotated[str, Depends(get_action_token_from_bearer)],
    uc: Annotated[
        ConfirmResetPasswordUseCase,
        Depends(get_confirm_reset_password_uc),
    ],
) -> dict[str, str]:
    await uc.execute(token=token, req=payload)
    return {"message": "Password updated successfully."}