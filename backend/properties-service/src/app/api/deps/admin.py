import uuid
from collections.abc import Awaitable, Callable

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.listing import (
    get_cache_port,
    get_catalog_gateway,
    get_storage_port,
    get_users_gateway,
)
from app.db import engine
from app.schemas.principal import Principal
from app.services.admin.adapters.sql_unit_of_work import SqlAdminUnitOfWork
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
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
from app.services.admin.use_cases.promotions.list_by_property import ListPromotionsByPropertyUseCase
from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.storage import StoragePort
from app.workers.bulk_create_properties_worker import BulkCreatePropertiesWorker


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_admin_uow(session: Session = Depends(get_session)) -> AdminUnitOfWork:
    return SqlAdminUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_admin_properties_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
) -> GetPropertiesAdminUseCase:
    return GetPropertiesAdminUseCase(uow=uow)


def get_admin_property_detail_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetPropertyDetailAdminUseCase:
    return GetPropertyDetailAdminUseCase(uow=uow, cache=cache)


def get_set_status_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> SetPropertyStatusUseCase:
    return SetPropertyStatusUseCase(uow=uow, cache=cache)


def get_verify_property_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> VerifyPropertyUseCase:
    return VerifyPropertyUseCase(uow=uow, cache=cache)


def get_set_estimated_price_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
) -> SetEstimatedPriceUseCase:
    return SetEstimatedPriceUseCase(uow=uow)


def get_list_all_promotions_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> ListAllPromotionsUseCase:
    return ListAllPromotionsUseCase(uow=uow, cache=cache)


def get_list_promotions_by_property_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> ListPromotionsByPropertyUseCase:
    return ListPromotionsByPropertyUseCase(uow=uow, cache=cache)


def get_create_promotion_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreatePromotionUseCase:
    return CreatePromotionUseCase(uow=uow, cache=cache)


def get_delete_promotion_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
    cache: CachePort = Depends(get_cache_port),
) -> DeletePromotionUseCase:
    return DeletePromotionUseCase(uow=uow, cache=cache)


def get_bulk_create_properties_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
) -> BulkCreatePropertiesUseCase:
    return BulkCreatePropertiesUseCase(uow=uow)


def get_bulk_job_status_uc(
    uow: AdminUnitOfWork = Depends(get_admin_uow),
) -> GetBulkJobStatusUseCase:
    return GetBulkJobStatusUseCase(uow=uow)


def get_request_bulk_upload_url_uc(
    storage: StoragePort = Depends(get_storage_port),
) -> RequestBulkUploadUrlUseCase:
    return RequestBulkUploadUrlUseCase(storage=storage)


# -------------------------------------------------------------------------
# Background runners
# -------------------------------------------------------------------------

async def run_bulk_create_properties(*, principal: Principal, job_id: uuid.UUID) -> None:
    # Own session scoped to the background task, not to the request that scheduled it.
    with Session(engine) as session:
        worker = BulkCreatePropertiesWorker(
            uow = SqlAdminUnitOfWork(session=session),
            catalog = get_catalog_gateway(),
            users = get_users_gateway(),
            storage = get_storage_port(),
        )
        await worker.execute(principal=principal, job_id=job_id)


def get_bulk_create_properties_runner() -> Callable[..., Awaitable[None]]:
    return run_bulk_create_properties
