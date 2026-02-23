from app.services.geo_resolution.ports.geocoding_gateway import GeocodingGateway
from app.services.geo_resolution.schemas.geocoding import GeocodingResult
from app.core.exceptions.geo_resolution import GeoResolutionNotFoundError

from app.integrations.georef.mapbox.georeferentiation import GeoreferentiationClient


class GeocodingAdapter(GeocodingGateway):
    """Adapter HTTP para geocoding (implementación con proveedor externo)."""

    def __init__(self, georef_client: GeoreferentiationClient):
        self.client = georef_client

    async def forward_geocode(self, *, query: str, country_code: str) -> GeocodingResult:
        geojson = await self.client.forward_geocoding(address=query, country_code=country_code)
        features = geojson.get("features", [])
        if not features:
            raise GeoResolutionNotFoundError(address=query)

        feature = features[0]
        coords = feature["geometry"]["coordinates"]

        return GeocodingResult(
            latitude=coords[1],
            longitude=coords[0],
            formatted_address=feature["properties"].get("full_address"),
        )
