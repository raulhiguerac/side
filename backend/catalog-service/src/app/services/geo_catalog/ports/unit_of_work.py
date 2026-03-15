from typing import Protocol

from app.services.geo_catalog.ports.countries_repository import CountryRepository
from app.services.geo_catalog.ports.locality_repository import LocalityRepository
from app.services.geo_catalog.ports.neighborhood_repository import (
    NeighborhoodRepository,
)


class GeoCatalogUnitOfWork(Protocol):
    countries: CountryRepository
    localities: LocalityRepository
    neighborhoods: NeighborhoodRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
