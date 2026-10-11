from fastapi import Depends

from app.api.deps.catalog_admin.uow import get_uow
from app.api.deps.geo_catalog import get_cache_port
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.use_cases.locality.create import CreateLocalityUseCase
from app.services.catalog_admin.use_cases.locality.list_all import ListLocalitiesUseCase
from app.services.catalog_admin.use_cases.locality.update import UpdateLocalityUseCase
from app.services.shared.ports.cache import CachePort


def list_localities_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
) -> ListLocalitiesUseCase:
    return ListLocalitiesUseCase(uow=uow)


def create_locality_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateLocalityUseCase:
    return CreateLocalityUseCase(uow=uow, cache_client=cache)


def update_locality_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateLocalityUseCase:
    return UpdateLocalityUseCase(uow=uow, cache_client=cache)
