import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps.auth import get_current_principal
from app.api.deps.upload_validation import validate_profile_photo_upload
from app.api.deps.user_use_cases import (
    get_current_profile_uc,
    get_profile_by_id_uc,
    get_update_current_profile_photo_uc,
    get_update_current_profile_uc,
)
from app.schemas.common import Principal
from app.services.user.schemas.current import CurrentUserProfileOut
from app.services.user.schemas.photo import PhotoUploadOut
from app.services.user.schemas.update import UpdateRequest
from app.services.user.use_cases.profile.get_current_profile import (
    GetCurrentProfileUseCase,
)
from app.services.user.use_cases.profile.get_profile_by_id import GetProfileByIdUseCase
from app.services.user.use_cases.profile.update_current_profile import (
    UpdateCurrentProfileUseCase,
)
from app.services.user.use_cases.profile.upload_profile_photo import (
    UpdateCurrentProfilePhotoUseCase,
)

router = APIRouter(prefix="/users", tags=["users"])


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
