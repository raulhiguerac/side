from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.geo_catalog import get_cache_port
from app.services.shared.ports.cache import CachePort
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.adapters.sql_unit_of_work import SqlCatalogAdminUnitOfWork

from app.services.catalog_admin.use_cases.create_country import CreateCountryUseCase
from app.services.catalog_admin.use_cases.create_admin_division import CreateAdminDivisionUseCase
from app.services.catalog_admin.use_cases.create_locality import CreateLocalityUseCase
from app.services.catalog_admin.use_cases.create_neighborhood import CreateNeighborhoodUseCase
from app.services.catalog_admin.use_cases.update_country import UpdateCountryUseCase
from app.services.catalog_admin.use_cases.update_admin_division import UpdateAdminDivisionUseCase
from app.services.catalog_admin.use_cases.update_locality import UpdateLocalityUseCase
from app.services.catalog_admin.use_cases.update_neighborhood import UpdateNeighborhoodUseCase


def get_uow(session: Session = Depends(get_session)) -> CatalogAdminUnitOfWork:
    return SqlCatalogAdminUnitOfWork(session=session)


def create_country_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateCountryUseCase:
    return CreateCountryUseCase(uow=uow, cache_client=cache)


def create_admin_division_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateAdminDivisionUseCase:
    return CreateAdminDivisionUseCase(uow=uow, cache_client=cache)


def create_locality_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateLocalityUseCase:
    return CreateLocalityUseCase(uow=uow, cache_client=cache)


def create_neighborhood_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateNeighborhoodUseCase:
    return CreateNeighborhoodUseCase(uow=uow, cache_client=cache)


def update_country_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateCountryUseCase:
    return UpdateCountryUseCase(uow=uow, cache_client=cache)


def update_admin_division_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateAdminDivisionUseCase:
    return UpdateAdminDivisionUseCase(uow=uow, cache_client=cache)


def update_locality_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateLocalityUseCase:
    return UpdateLocalityUseCase(uow=uow, cache_client=cache)


def update_neighborhood_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateNeighborhoodUseCase:
    return UpdateNeighborhoodUseCase(uow=uow, cache_client=cache)
