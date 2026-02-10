from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session

from app.services.shared.ports.cache import CachePort
from app.services.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from app.integrations.cache.redis.cache import CacheClient

from app.services.geo_catalog.ports.unit_of_work import GeoCatalogUnitOfWork
from app.services.geo_catalog.adapters.sql_unit_of_work import SqlGeoCatalogUnitOfWork

from app.services.geo_catalog.use_cases.get_locality import GetLocalitiesUseCase
from app.services.geo_catalog.use_cases.get_locality_by_id import GetLocalityByIdUseCase
from app.services.geo_catalog.use_cases.get_neighborhoods_by_locality import GetNeighborhoodsByLocalityUseCase
from app.services.geo_catalog.use_cases.get_neighborhood_by_id import GetNeighborhoodByIdUseCase


# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> GeoCatalogUnitOfWork:
    return SqlGeoCatalogUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_localities_uc(
    uow: GeoCatalogUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetLocalitiesUseCase:
    return GetLocalitiesUseCase(uow=uow, cache_client=cache)

def get_locality_by_id_uc(
    uow: GeoCatalogUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetLocalityByIdUseCase:
    return GetLocalityByIdUseCase(uow=uow, cache_client=cache)

def get_neighborhoods_by_locality_uc(
    uow: GeoCatalogUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetNeighborhoodsByLocalityUseCase:
    return GetNeighborhoodsByLocalityUseCase(uow=uow, cache_client=cache)

def get_neighborhood_by_id_uc(
    uow: GeoCatalogUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetNeighborhoodByIdUseCase:
    return GetNeighborhoodByIdUseCase(uow=uow, cache_client=cache)
