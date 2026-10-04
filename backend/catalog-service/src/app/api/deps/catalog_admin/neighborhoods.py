from fastapi import Depends

from app.api.deps.catalog_admin.uow import get_uow
from app.api.deps.geo_catalog import get_cache_port
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.use_cases.neighborhood.bulk_create import (
    BulkCreateNeighborhoodsUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.bulk_enrich_geometries import (
    BulkEnrichNeighborhoodGeometriesUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.create import (
    CreateNeighborhoodUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.enrich_geometry import (
    EnrichNeighborhoodGeometryUseCase,
)
from app.services.catalog_admin.use_cases.neighborhood.update import (
    UpdateNeighborhoodUseCase,
)
from app.services.shared.ports.cache import CachePort


def create_neighborhood_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CreateNeighborhoodUseCase:
    return CreateNeighborhoodUseCase(uow=uow, cache_client=cache)


def update_neighborhood_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdateNeighborhoodUseCase:
    return UpdateNeighborhoodUseCase(uow=uow, cache_client=cache)


def enrich_neighborhood_geometry_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> EnrichNeighborhoodGeometryUseCase:
    return EnrichNeighborhoodGeometryUseCase(uow=uow, cache_client=cache)


def bulk_create_neighborhoods_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> BulkCreateNeighborhoodsUseCase:
    return BulkCreateNeighborhoodsUseCase(uow=uow, cache_client=cache)


def bulk_enrich_neighborhood_geometries_uc(
    uow: CatalogAdminUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> BulkEnrichNeighborhoodGeometriesUseCase:
    return BulkEnrichNeighborhoodGeometriesUseCase(uow=uow, cache_client=cache)
