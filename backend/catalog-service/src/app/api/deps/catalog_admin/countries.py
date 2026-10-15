from fastapi import Depends

from app.api.deps.catalog_admin.uow import get_uow
from app.api.deps.geo_catalog import get_cache_port
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.use_cases.country.create import CreateCountryUseCase
from app.services.catalog_admin.use_cases.country.list_all import ListCountriesUseCase
from app.services.catalog_admin.use_cases.country.update import UpdateCountryUseCase
from app.services.shared.ports.cache import CachePort


def list_countries_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
) -> ListCountriesUseCase:
    return ListCountriesUseCase(uow=uow)


def create_country_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateCountryUseCase:
    return CreateCountryUseCase(uow=uow, cache_client=cache)


def update_country_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateCountryUseCase:
    return UpdateCountryUseCase(uow=uow, cache_client=cache)
