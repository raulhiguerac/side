from app.services.geo_resolution.ports.geocoding_gateway import GeocodingGateway
from app.services.geo_resolution.schemas.geocoding import GeocodingResult

from app.integrations.georef.mapbox.georeferentiation import GeoreferentiationClient


class GeocodingAdapter(GeocodingGateway):
    """Adapter HTTP para geocoding (implementación con proveedor externo)."""

    def __init__(self, georef_client: GeoreferentiationClient):
        self.client = georef_client

    async def forward_geocode(self, *, query: str) -> GeocodingResult:
        geojson = await self.client.forward_geocoding(address=query)
        feature = geojson["features"][0]
        coords = feature["geometry"]["coordinates"]

        return GeocodingResult(
            latitude=coords[1],
            longitude=coords[0],
            formatted_address=feature["properties"].get("place_name"),
        )
