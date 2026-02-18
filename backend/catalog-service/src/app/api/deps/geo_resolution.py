from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.geo_catalog import get_cache_port

from app.services.shared.ports.cache import CachePort

from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.adapters.sql_unit_of_work import SqlGeoResolutionUnitOfWork

from app.services.geo_resolution.ports.geocoding_gateway import GeocodingGateway
from app.services.geo_resolution.adapters.geocoding import GeocodingAdapter

from app.services.geo_resolution.ports.poi_provider_gateway import PoiProviderGateway
from app.services.geo_resolution.adapters.poi_provider import PoiProviderAdapter

from app.integrations.georef.mapbox.georeferentiation import GeoreferentiationClient
from app.integrations.georef.pois.overpass import PoiClient

from app.services.geo_resolution.use_cases.resolve_neighborhood import ResolveNeighborhoodUseCase
from app.services.geo_resolution.use_cases.resolve_poi import ResolvePoiUseCase


# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_georef_client() -> GeoreferentiationClient:
    return GeoreferentiationClient()


@lru_cache(maxsize=1)
def get_geocoding_gateway() -> GeocodingGateway:
    return GeocodingAdapter(georef_client=get_georef_client())


@lru_cache(maxsize=1)
def get_poi_client() -> PoiClient:
    return PoiClient()


@lru_cache(maxsize=1)
def get_poi_provider() -> PoiProviderGateway:
    return PoiProviderAdapter(client=get_poi_client())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> GeoResolutionUnitOfWork:
    return SqlGeoResolutionUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def resolve_neighborhood_uc(
    uow: GeoResolutionUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    georef: GeocodingGateway = Depends(get_geocoding_gateway),
) -> ResolveNeighborhoodUseCase:
    return ResolveNeighborhoodUseCase(uow=uow, cache_client=cache, georef=georef)


def resolve_poi_uc(
    uow: GeoResolutionUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    poi_provider: PoiProviderGateway = Depends(get_poi_provider),
) -> ResolvePoiUseCase:
    return ResolvePoiUseCase(uow=uow, cache_client=cache, poi_provider=poi_provider)
