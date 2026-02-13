from typing import Any, Protocol


class MapboxGateway(Protocol):
    """Puerto hacia la API de Mapbox (geocoding / search)."""

    async def forward_geocode(self, *, query: str, proximity: tuple[float, float] | None = None) -> list[dict[str, Any]]: ...

    async def reverse_geocode(self, *, latitude: float, longitude: float) -> list[dict[str, Any]]: ...
