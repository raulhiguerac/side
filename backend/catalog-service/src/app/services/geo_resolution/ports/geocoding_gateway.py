from typing import Protocol

from app.services.geo_resolution.schemas.geocoding import GeocodingResult


class GeocodingGateway(Protocol):
    """Puerto hacia un proveedor de geocoding (Mapbox, Google Maps, etc.)."""

    async def forward_geocode(self, *, query: str) -> GeocodingResult: ...

    async def reverse_geocode(self, *, latitude: float, longitude: float) -> GeocodingResult: ...
