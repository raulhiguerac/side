from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps.auth import get_current_principal
from app.api.deps.upload_validation import validate_profile_photo_upload
from app.api.deps.user_use_cases import (
    get_current_account_uc,
    get_current_profile_uc,
    get_update_current_profile_photo_uc,
    get_update_current_profile_uc,
    get_deactivate_current_account_uc,
)

from app.api.deps.auth_use_cases import (
    get_logout_account_uc
)

from app.api.deps.auth import (
    get_refresh_token_from_cookie_optional, 
    get_current_principal
)

from app.schemas.auth import Principal, RefreshToken
from app.schemas.user import (
    CurrentUserOut,
    CurrentUserProfileOut,
    PhotoUploadOut,
    UpdateRequest,
)

from app.services.user.use_cases.get_current_account import GetCurrentAccountUseCase
from app.services.user.use_cases.get_current_profile import GetCurrentProfileUseCase
from app.services.user.use_cases.upload_profile_photo import (
    UpdateCurrentProfilePhotoUseCase,
)
from app.services.user.use_cases.update_current_profile import (
    UpdateCurrentProfileUseCase,
)
from app.services.user.use_cases.deactivate_current_account import (
    DeactivateCurrentAccountUseCase,
)
from app.services.auth.use_cases.logout import (
    LogoutUseCase,
)

router = APIRouter(prefix="/users", tags=["profile"])


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
):
    return await uc.execute(principal=principal)


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
):
    return await uc.execute(principal=principal)


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
):
    return await uc.execute(
        file=file.file,
        content_type=validated_mime,
        principal=principal,
    )


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
    uc: Annotated[
        UpdateCurrentProfileUseCase,
        Depends(get_update_current_profile_uc),
    ],
):
    return await uc.execute(
        principal=principal,
        req=req,
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
    uc_logout: Annotated[
        LogoutUseCase,
        Depends(get_logout_account_uc),
    ],
) -> None:
    await uc.execute(principal=principal)

    try:
        await uc_logout.logout(
            refresh_token=refresh.refresh_token if refresh else None
        )
    except Exception:
        pass
