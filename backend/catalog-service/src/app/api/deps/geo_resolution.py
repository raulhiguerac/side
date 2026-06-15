from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.api.deps.geo_catalog import get_cache_port
from app.integrations.georef.mapbox.georeferentiation import GeoreferentiationClient
from app.integrations.georef.ors.routing import OrsRoutingClient
from app.integrations.georef.pois.overpass import PoiClient
from app.services.geo_resolution.adapters.geocoding.mapbox import GeocodingAdapter
from app.services.geo_resolution.adapters.poi.overpass import PoiProviderAdapter
from app.services.geo_resolution.adapters.routing.ors import OrsRoutingAdapter
from app.services.geo_resolution.adapters.sql.unit_of_work import (
    SqlGeoResolutionUnitOfWork,
)
from app.services.geo_resolution.ports.geocoding.gateway import GeocodingGateway
from app.services.geo_resolution.ports.poi.gateway import PoiProviderGateway
from app.services.geo_resolution.ports.routing.gateway import RoutingGateway
from app.services.geo_resolution.ports.unit_of_work import GeoResolutionUnitOfWork
from app.services.geo_resolution.use_cases.resolve_location_by_coordinates import (
    ResolveLocationByCoordinatesUseCase,
)
from app.services.geo_resolution.use_cases.resolve_neighborhood import (
    ResolveNeighborhoodUseCase,
)
from app.services.geo_resolution.use_cases.resolve_isochrone import ResolveIsochroneUseCase
from app.services.geo_resolution.use_cases.resolve_poi import ResolvePoiUseCase
from app.services.shared.ports.cache import CachePort

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


@lru_cache(maxsize=1)
def get_ors_client() -> OrsRoutingClient:
    return OrsRoutingClient()


@lru_cache(maxsize=1)
def get_routing_gateway() -> RoutingGateway:
    return OrsRoutingAdapter(client=get_ors_client())


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


def resolve_location_by_coordinates_uc(
    uow: GeoResolutionUnitOfWork = Depends(get_uow),
) -> ResolveLocationByCoordinatesUseCase:
    return ResolveLocationByCoordinatesUseCase(uow=uow)


def resolve_isochrone_uc(
    uow: GeoResolutionUnitOfWork = Depends(get_uow),
    gateway: RoutingGateway = Depends(get_routing_gateway),
) -> ResolveIsochroneUseCase:
    return ResolveIsochroneUseCase(uow=uow, gateway=gateway)
