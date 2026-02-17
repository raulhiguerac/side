from typing import Protocol

class PoiProviderGateway(Protocol):
    async def get_pois_by_bbox(self, *, bbox: list[float]) -> dict: ...
