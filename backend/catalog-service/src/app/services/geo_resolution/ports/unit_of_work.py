from typing import Protocol

from app.services.geo_resolution.ports.fetch_zone_repository import FetchZoneRepository
from app.services.geo_resolution.ports.georeferentiation_repository import (
    GeoreferentiationRepository,
)
from app.services.geo_resolution.ports.poi_repository import PoiRepository


class GeoResolutionUnitOfWork(Protocol):
    pois: PoiRepository
    fetch_zones: FetchZoneRepository
    georef: GeoreferentiationRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
