import uuid
from typing import Protocol

from app.models.location import PointOfInterest


class PoiProviderGateway(Protocol):
    async def get_pois_by_bbox(
        self,
        *,
        bbox: list[float],
        locality_id: uuid.UUID,
        neighborhood_id: uuid.UUID,
        h3_index: str,
    ) -> list[PointOfInterest]: ...
