import uuid
from typing import Protocol

from app.services.shared.schemas.catalog_schemas import NeighborhoodInfo


class CatalogGateway(Protocol):
    async def get_neighborhood(self, *, neighborhood_id: uuid.UUID) -> NeighborhoodInfo: ...
