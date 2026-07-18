import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps.action_token import get_action_token_from_bearer
from app.api.deps.auth import (
    get_current_principal,
    get_refresh_token_from_cookie_optional,
)
from app.api.deps.auth_use_cases import get_logout_account_uc
from app.api.deps.upload_validation import validate_profile_photo_upload
from app.api.deps.user_use_cases import (
    get_confirm_reactivation_uc,
    get_current_account_uc,
    get_current_profile_uc,
    get_deactivate_current_account_uc,
    get_profile_by_id_uc,
    get_request_reactivation_uc,
    get_update_current_profile_photo_uc,
    get_update_current_profile_uc,
    get_user_interests_uc,
)
from app.schemas.common import Principal
from app.services.auth.schemas.tokens import RefreshToken
from app.services.auth.use_cases.logout import LogoutUseCase
from app.services.user.schemas.current import (
    CurrentUserOut,
    CurrentUserProfileOut,
    UserInterestsResponse,
)
from app.services.user.schemas.photo import PhotoUploadOut
from app.services.user.schemas.reactivation import RequestReactivationIn
from app.services.user.schemas.update import UpdateRequest
from app.services.user.use_cases.account.deactivate_current_account import (
    DeactivateCurrentAccountUseCase,
)
from app.services.user.use_cases.account.get_current_account import (
    GetCurrentAccountUseCase,
)
from app.services.user.use_cases.account.get_interests import GetUserInterestsUseCase
from app.services.user.use_cases.account.reactivate_current_account import (
    ConfirmReactivationUseCase,
)
from app.services.user.use_cases.account.request_account_reactivation import (
    RequestReactivationUseCase,
)
from app.services.user.use_cases.profile.get_current_profile import (
    GetCurrentProfileUseCase,
)
from app.services.user.use_cases.profile.get_profile_by_id import (
    GetProfileByIdUseCase,
)
from app.services.user.use_cases.profile.update_current_profile import (
    UpdateCurrentProfileUseCase,
)
from app.services.user.use_cases.profile.upload_profile_photo import (
    UpdateCurrentProfilePhotoUseCase,
)

router = APIRouter(prefix="/users", tags=["users"])


# -------------------------------------------------------------------------
# Current user
# -------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=CurrentUserOut,
    status_code=status.HTTP_200_OK,
)
async def get_current_user(
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[GetCurrentAccountUseCase, Depends(get_current_account_uc)],
) -> CurrentUserOut:
    return await uc.execute(principal=principal)


# -------------------------------------------------------------------------
# Interests
# -------------------------------------------------------------------------


@router.get(
    "/me/interests",
    response_model=UserInterestsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_interests(
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[GetUserInterestsUseCase, Depends(get_user_interests_uc)],
) -> UserInterestsResponse:
    return await uc.execute(account_id=principal.sub)


# -------------------------------------------------------------------------
# Profile (read)
# -------------------------------------------------------------------------


@router.get(
    "/me/profile",
    response_model=CurrentUserProfileOut,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[GetCurrentProfileUseCase, Depends(get_current_profile_uc)],
) -> CurrentUserProfileOut:
    return await uc.execute(account_id=principal.sub)


# -------------------------------------------------------------------------
# Profile (public read)
# -------------------------------------------------------------------------


@router.get(
    "/profiles/{account_id}",
    response_model=CurrentUserProfileOut,
    status_code=status.HTTP_200_OK,
)
async def get_user_profile_by_id(
    account_id: uuid.UUID,
    uc: Annotated[GetProfileByIdUseCase, Depends(get_profile_by_id_uc)],
) -> CurrentUserProfileOut:
    return await uc.execute(account_id=account_id)


# -------------------------------------------------------------------------
# Profile (update)
# -------------------------------------------------------------------------


@router.patch(
    "/me/profile",
    response_model=CurrentUserProfileOut,
    status_code=status.HTTP_200_OK,
)
async def update_user_profile(
    req: UpdateRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[UpdateCurrentProfileUseCase, Depends(get_update_current_profile_uc)],
) -> CurrentUserProfileOut:
    return await uc.execute(principal=principal, req=req)


# -------------------------------------------------------------------------
# Profile photo (write)
# -------------------------------------------------------------------------


@router.post(
    "/me/profile/photo",
    response_model=PhotoUploadOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_user_profile_photo(
    file: Annotated[UploadFile, File(...)],
    validated_mime: Annotated[str, Depends(validate_profile_photo_upload)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[
        UpdateCurrentProfilePhotoUseCase,
        Depends(get_update_current_profile_photo_uc),
    ],
) -> PhotoUploadOut:
    return await uc.execute(
        file=file.file,
        content_type=validated_mime,
        principal=principal,
    )


# -------------------------------------------------------------------------
# Account (deactivate)
# -------------------------------------------------------------------------


@router.post(
    "/me/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_user_account(
    principal: Annotated[Principal, Depends(get_current_principal)],
    refresh: Annotated[
        RefreshToken | None,
        Depends(get_refresh_token_from_cookie_optional),
    ],
    uc: Annotated[
        DeactivateCurrentAccountUseCase,
        Depends(get_deactivate_current_account_uc),
    ],
    uc_logout: Annotated[LogoutUseCase, Depends(get_logout_account_uc)],
) -> None:
    await uc.execute(principal=principal)

    # Best-effort logout: never block account deactivation if logout fails
    try:
        await uc_logout.logout(
            refresh_token=refresh.refresh_token if refresh else None
        )
    except Exception:
        pass


# -------------------------------------------------------------------------
# Account (reactivation)
# -------------------------------------------------------------------------


@router.post(
    "/reactivation/request",
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_account_reactivation(
    req: RequestReactivationIn,
    uc: Annotated[RequestReactivationUseCase, Depends(get_request_reactivation_uc)],
) -> dict[str, str]:
    await uc.execute(email=req.email)
    return {
        "message": "If the account exists, a reactivation email will be sent shortly."
    }


@router.post(
    "/reactivation/confirm",
    status_code=status.HTTP_200_OK,
)
async def confirm_account_reactivation(
    token: Annotated[str, Depends(get_action_token_from_bearer)],
    uc: Annotated[ConfirmReactivationUseCase, Depends(get_confirm_reactivation_uc)],
) -> dict[str, str]:
    await uc.execute(token=token)
    return {"status": "reactivated"}
