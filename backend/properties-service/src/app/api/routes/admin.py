import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.deps.admin import (
    get_admin_properties_uc,
    get_admin_property_detail_uc,
    get_bulk_create_properties_runner,
    get_bulk_create_properties_uc,
    get_bulk_job_status_uc,
    get_create_promotion_uc,
    get_delete_promotion_uc,
    get_list_all_promotions_uc,
    get_request_bulk_upload_url_uc,
    get_set_estimated_price_uc,
    get_set_status_uc,
    get_verify_property_uc,
)
from app.api.deps.auth import require_admin
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import (
    AdminPromotionsPage,
    AdminPropertiesPage,
    AdminPropertyDetailSchema,
    BulkCreatePropertiesRequest,
    BulkJobAccepted,
    BulkJobStatusResponse,
    BulkUploadUrlRequest,
    BulkUploadUrlResponse,
    CreatePromotionRequest,
    GetPromotionsAdminRequest,
    GetPropertiesAdminRequest,
    SetEstimatedPriceRequest,
    SetStatusRequest,
    VerifyPropertyRequest,
)
from app.services.admin.use_cases.bulk_create_properties import BulkCreatePropertiesUseCase
from app.services.admin.use_cases.estimated_price.set_estimated_price import SetEstimatedPriceUseCase
from app.services.admin.use_cases.get_bulk_job_status import GetBulkJobStatusUseCase
from app.services.admin.use_cases.request_bulk_upload_url import RequestBulkUploadUrlUseCase
from app.services.admin.use_cases.get_properties import GetPropertiesAdminUseCase
from app.services.admin.use_cases.get_property_detail import GetPropertyDetailAdminUseCase
from app.services.admin.use_cases.moderation.set_status import SetPropertyStatusUseCase
from app.services.admin.use_cases.moderation.verify import VerifyPropertyUseCase
from app.services.admin.use_cases.promotions.create import CreatePromotionUseCase
from app.services.admin.use_cases.promotions.delete import DeletePromotionUseCase
from app.services.admin.use_cases.promotions.list_all import ListAllPromotionsUseCase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# -------------------------------------------------------------------------
# Properties
# -------------------------------------------------------------------------

@router.post(
    "/properties/bulk/upload-url",
    response_model=BulkUploadUrlResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_bulk_upload_url(
    req: BulkUploadUrlRequest,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[RequestBulkUploadUrlUseCase, Depends(get_request_bulk_upload_url_uc)],
) -> BulkUploadUrlResponse:
    """Step 1 of the bulk import: get a presigned PUT, upload the CSV straight
    to storage, then POST the returned storage_key to /properties/bulk."""
    result = await uc.execute(principal=principal, request=req)
    # `filename` is a reserved LogRecord attribute — passing it in `extra` raises
    # KeyError inside logging.makeRecord, before any formatter runs.
    logger.info(
        "bulk upload url issued",
        extra={"upload_filename": req.filename, "storage_key": result.storage_key, "ttl_s": result.expires_in},
    )
    return result


@router.post(
    "/properties/bulk",
    response_model=BulkJobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def bulk_create_properties(
    payload: BulkCreatePropertiesRequest,
    background_tasks: BackgroundTasks,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[BulkCreatePropertiesUseCase, Depends(get_bulk_create_properties_uc)],
    runner: Annotated[Callable[..., Awaitable[None]], Depends(get_bulk_create_properties_runner)],
) -> BulkJobAccepted:
    """The CSV is uploaded straight to storage by the front with a presigned PUT;
    here we only register the job and hand it off to the background worker."""
    batch_id = await uc.execute(
        principal = principal,
        storage_key = payload.storage_key,
        retry_job_id = payload.retry_of_job_id,
    )
    background_tasks.add_task(runner, principal=principal, job_id=batch_id)
    logger.info(
        "bulk job accepted, worker scheduled",
        extra={
            "job_id": str(batch_id),
            "storage_key": payload.storage_key,
            "retry_of": str(payload.retry_of_job_id) if payload.retry_of_job_id else None,
        },
    )

    return BulkJobAccepted(batch_id=batch_id)


@router.get(
    "/properties/bulk/{job_id}/status",
    response_model=BulkJobStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_bulk_job_status(
    job_id: uuid.UUID,
    uc: Annotated[GetBulkJobStatusUseCase, Depends(get_bulk_job_status_uc)],
) -> BulkJobStatusResponse:
    return await uc.execute(job_id=job_id)


@router.get(
    "/properties",
    response_model=AdminPropertiesPage,
    status_code=status.HTTP_200_OK,
)
async def get_properties(
    filters: Annotated[GetPropertiesAdminRequest, Depends()],
    uc: Annotated[GetPropertiesAdminUseCase, Depends(get_admin_properties_uc)],
) -> AdminPropertiesPage:
    return await uc.execute(request=filters)


@router.get(
    "/properties/{property_id}",
    response_model=AdminPropertyDetailSchema,
    status_code=status.HTTP_200_OK,
)
async def get_property_detail(
    property_id: uuid.UUID,
    uc: Annotated[GetPropertyDetailAdminUseCase, Depends(get_admin_property_detail_uc)],
) -> AdminPropertyDetailSchema:
    return await uc.execute(property_id=property_id)


@router.patch(
    "/properties/{property_id}/status",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def set_property_status(
    property_id: uuid.UUID,
    req: SetStatusRequest,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[SetPropertyStatusUseCase, Depends(get_set_status_uc)],
) -> None:
    await uc.execute(
        principal = principal,
        property_id = property_id,
        target_status = req.status,
    )


@router.patch(
    "/properties/{property_id}/verification",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def verify_property(
    property_id: uuid.UUID,
    req: VerifyPropertyRequest,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[VerifyPropertyUseCase, Depends(get_verify_property_uc)],
) -> None:
    await uc.execute(
        principal = principal,
        property_id = property_id,
        request = req,
    )


@router.post(
    "/properties/{property_id}/estimated-price",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def set_estimated_price(
    property_id: uuid.UUID,
    req: SetEstimatedPriceRequest,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[SetEstimatedPriceUseCase, Depends(get_set_estimated_price_uc)],
) -> None:
    await uc.execute(principal=principal, property_id=property_id, estimated_price=req.estimated_price)


# -------------------------------------------------------------------------
# Promotions
# -------------------------------------------------------------------------

@router.get(
    "/promotions",
    response_model=AdminPromotionsPage,
    status_code=status.HTTP_200_OK,
)
async def list_all_promotions(
    filters: Annotated[GetPromotionsAdminRequest, Depends()],
    uc: Annotated[ListAllPromotionsUseCase, Depends(get_list_all_promotions_uc)],
) -> AdminPromotionsPage:
    return await uc.execute(request=filters)


@router.post(
    "/promotions",
    status_code=status.HTTP_201_CREATED,
)
async def create_promotion(
    req: CreatePromotionRequest,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[CreatePromotionUseCase, Depends(get_create_promotion_uc)],
) -> None:
    await uc.execute(principal=principal, promotion_request=req)


@router.delete(
    "/properties/{property_id}/promotions",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_promotion(
    property_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_admin)],
    uc: Annotated[DeletePromotionUseCase, Depends(get_delete_promotion_uc)],
) -> None:
    await uc.execute(principal=principal, property_id=property_id)
