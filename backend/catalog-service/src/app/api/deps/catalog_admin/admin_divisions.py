from fastapi import Depends

from app.api.deps.catalog_admin.uow import get_uow
from app.api.deps.geo_catalog import get_cache_port
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.use_cases.admin_division.create import (
    CreateAdminDivisionUseCase,
)
from app.services.catalog_admin.use_cases.admin_division.list_all import (
    ListAdminDivisionsUseCase,
)
from app.services.catalog_admin.use_cases.admin_division.update import (
    UpdateAdminDivisionUseCase,
)
from app.services.shared.ports.cache import CachePort


def list_admin_divisions_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
) -> ListAdminDivisionsUseCase:
    return ListAdminDivisionsUseCase(uow=uow)


def create_admin_division_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateAdminDivisionUseCase:
    return CreateAdminDivisionUseCase(uow=uow, cache_client=cache)


def update_admin_division_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateAdminDivisionUseCase:
    return UpdateAdminDivisionUseCase(uow=uow, cache_client=cache)
