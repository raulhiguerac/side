from typing import Protocol

from app.services.geo_resolution.schemas.geocoding import GeocodingResult


class GeocodingGateway(Protocol):
    """Puerto hacia un proveedor de geocoding (Mapbox, Google Maps, etc.)."""

    async def forward_geocode(self, *, query: str, country_code: str, proximity: tuple[float, float] | None = None) -> GeocodingResult: ...
