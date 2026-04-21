from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.listing import get_cache_port
from app.services.admin.adapters.sql_unit_of_work import SqlAdminUnitOfWork
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.use_cases.estimated_price.set_estimated_price import SetEstimatedPriceUseCase
from app.services.admin.use_cases.get_properties import GetPropertiesAdminUseCase
from app.services.admin.use_cases.get_property_detail import GetPropertyDetailAdminUseCase
from app.services.admin.use_cases.moderation.set_status import SetPropertyStatusUseCase
from app.services.admin.use_cases.moderation.verify import VerifyPropertyUseCase
from app.services.admin.use_cases.promotions.create import CreatePromotionUseCase
from app.services.admin.use_cases.promotions.delete import DeletePromotionUseCase
from app.services.admin.use_cases.promotions.list_all import ListAllPromotionsUseCase
from app.services.admin.use_cases.promotions.list_by_property import ListPromotionsByPropertyUseCase
from app.services.shared.ports.cache import CachePort


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
