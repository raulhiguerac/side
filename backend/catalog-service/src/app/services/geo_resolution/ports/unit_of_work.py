from typing import Protocol

from app.services.geo_resolution.ports.poi_repository import PoiRepository


class GeoResolutionUnitOfWork(Protocol):
    pois: PoiRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
