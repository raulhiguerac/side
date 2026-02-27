import uuid

from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork
from app.services.catalog_admin.schemas.neighborhood import BulkEnrichNeighborhoodGeometriesResult
from app.services.shared.ports.cache import CachePort


class BulkEnrichNeighborhoodGeometriesUseCase:
    def __init__(self, *, uow: CatalogAdminUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(self, *, locality_id: uuid.UUID, geojson: dict) -> BulkEnrichNeighborhoodGeometriesResult:
        ...
