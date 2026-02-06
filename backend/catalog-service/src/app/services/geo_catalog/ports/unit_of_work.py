from typing import Protocol

from app.services.geo_catalog.ports.locality_repository import LocalityRepository


class GeoCatalogUnitOfWork(Protocol):
    localities: LocalityRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
