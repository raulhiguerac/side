from app.services.geo_resolution.ports.poi_provider_gateway import PoiProviderGateway
from app.integrations.georef.pois.overpass import PoiClient


class PoiProviderAdapter(PoiProviderGateway):

    def __init__(self, client: PoiClient):
        self.client = client

    async def get_pois_by_bbox(self, *, bbox: list[float]) -> dict:
        return await self.client.get_pois_by_bbox(bbox=bbox)

