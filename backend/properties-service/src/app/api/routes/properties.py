import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status

from app.api.deps.auth import get_current_principal, get_current_principal_optional
from app.api.deps.listing import (
    get_confirm_image_uploads_uc,
    get_create_property_uc,
    get_delete_property_images_uc,
    get_delete_property_uc,
    get_my_properties_uc,
    get_property_uc,
    get_public_user_properties_uc,
    get_request_presigned_urls_uc,
    get_set_visibility_uc,
    get_update_property_uc,
)
from app.schemas.principal import Principal
from app.services.listing.schemas.listing_schemas import (
    ConfirmImagesRequest,
    CreatePropertyRequest,
    DeleteImagesRequest,
    PresignedUrlsRequest,
    PresignedUrlsResponse,
    UpdatePropertyRequest,
)
from app.services.listing.use_cases.images.confirm_image_uploads import ConfirmImageUploadsUseCase
from app.services.listing.use_cases.images.delete_property_images import DeletePropertyImagesUseCase
from app.services.listing.use_cases.images.request_presigned_urls import RequestPresignedUrlsUseCase
from app.services.listing.use_cases.property_core.create_property import CreatePropertyUseCase
from app.services.listing.use_cases.property_core.delete_property import DeletePropertyUseCase
from app.services.listing.use_cases.property_core.get_my_properties import GetMyPropertiesUseCase
from app.services.listing.use_cases.property_core.get_property import GetPropertyUseCase
from app.services.listing.use_cases.property_core.get_public_user_properties import GetPublicUserPropertiesUseCase
from app.services.listing.use_cases.property_core.set_property_visibility import SetPropertyVisibilityUseCase
from app.services.listing.use_cases.property_core.update_property import UpdatePropertyUseCase
from app.services.shared.schemas.property_card import PropertyCardSchema
from app.services.shared.schemas.property_detail import PropertyDetailSchema

router = APIRouter(prefix="/properties", tags=["properties"])


# -------------------------------------------------------------------------
# My properties (before /{property_id} to avoid shadowing)
# -------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=list[PropertyCardSchema],
    status_code=status.HTTP_200_OK,
)
async def get_my_properties(
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[GetMyPropertiesUseCase, Depends(get_my_properties_uc)],
) -> list[PropertyCardSchema]:
    return await uc.execute(principal=principal)


# -------------------------------------------------------------------------
# Public user properties
# -------------------------------------------------------------------------

@router.get(
    "/users/{user_id}",
    response_model=list[PropertyCardSchema],
    status_code=status.HTTP_200_OK,
)
async def get_public_user_properties(
    user_id: uuid.UUID,
    uc: Annotated[GetPublicUserPropertiesUseCase, Depends(get_public_user_properties_uc)],
) -> list[PropertyCardSchema]:
    return await uc.execute(user_id=user_id)


# -------------------------------------------------------------------------
# Presigned URLs (before /{property_id} to avoid shadowing)
# -------------------------------------------------------------------------

@router.post(
    "/images/presigned-urls",
    response_model=PresignedUrlsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_presigned_urls(
    req: PresignedUrlsRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[RequestPresignedUrlsUseCase, Depends(get_request_presigned_urls_uc)],
) -> PresignedUrlsResponse:
    return await uc.execute(principal=principal, request=req)


# -------------------------------------------------------------------------
# Property CRUD
# -------------------------------------------------------------------------

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_property(
    req: CreatePropertyRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[CreatePropertyUseCase, Depends(get_create_property_uc)],
) -> None:
    await uc.execute(principal=principal, property_fields=req)


@router.get(
    "/{property_id}",
    response_model=PropertyDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_property(
    property_id: uuid.UUID,
    principal: Annotated[Optional[Principal], Depends(get_current_principal_optional)],
    uc: Annotated[GetPropertyUseCase, Depends(get_property_uc)],
) -> PropertyDetailSchema:
    return await uc.execute(property_id=property_id, principal=principal)


@router.patch(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_property(
    property_id: uuid.UUID,
    req: UpdatePropertyRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[UpdatePropertyUseCase, Depends(get_update_property_uc)],
) -> None:
    await uc.execute(principal=principal, property_id=property_id, request=req)


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_property(
    property_id: uuid.UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[DeletePropertyUseCase, Depends(get_delete_property_uc)],
) -> None:
    await uc.execute(property_id=property_id, principal=principal)


@router.post(
    "/{property_id}/visibility",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def toggle_visibility(
    property_id: uuid.UUID,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[SetPropertyVisibilityUseCase, Depends(get_set_visibility_uc)],
) -> None:
    await uc.execute(property_id=property_id, principal=principal)


# -------------------------------------------------------------------------
# Images
# -------------------------------------------------------------------------

@router.post(
    "/{property_id}/images/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def confirm_image_uploads(
    property_id: uuid.UUID,
    req: ConfirmImagesRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[ConfirmImageUploadsUseCase, Depends(get_confirm_image_uploads_uc)],
) -> None:
    await uc.execute(
        principal=principal,
        property_id=property_id,
        batch_id=req.batch_id,
        confirmed_keys=req.confirmed_keys,
    )


@router.delete(
    "/{property_id}/images",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_property_images(
    property_id: uuid.UUID,
    req: DeleteImagesRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[DeletePropertyImagesUseCase, Depends(get_delete_property_images_uc)],
) -> None:
    await uc.execute(principal=principal, property_id=property_id, image_ids=req.image_ids)
