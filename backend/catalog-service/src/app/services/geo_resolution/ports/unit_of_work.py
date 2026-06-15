from typing import Protocol

from app.services.geo_resolution.ports.poi.repository import PoiRepository
from app.services.geo_resolution.ports.sql.fetch_zone_repository import FetchZoneRepository
from app.services.geo_resolution.ports.sql.georeferentiation_repository import (
    GeoreferentiationRepository,
)


class GeoResolutionUnitOfWork(Protocol):
    pois: PoiRepository
    fetch_zones: FetchZoneRepository
    georef: GeoreferentiationRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
