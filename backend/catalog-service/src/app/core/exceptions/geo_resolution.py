from typing import Any, Dict, Optional
from app.core.exceptions.base import BaseError


class GeoResolutionMisconfiguredError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Georeferentiation provider is misconfigured",
            code="GEO_RESOLUTION_MISCONFIGURED",
            cause=cause,
            context=context,
        )


class GeoResolutionUnavailableError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Georeferentiation provider is unreachable",
            code="GEO_RESOLUTION_UNAVAILABLE",
            cause=cause,
            context=context,
        )


class GeoResolutionBadRequestError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Invalid geocoding request",
            code="GEO_RESOLUTION_BAD_REQUEST",
            cause=cause,
            context=context,
        )


class GeoResolutionNotFoundError(BaseError):
    def __init__(self, *, address: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"No results found for address '{address}'",
            code="GEO_RESOLUTION_NOT_FOUND",
            context={"address": address, **(context or {})},
        )


class NeighborhoodResolutionError(BaseError):
    def __init__(self, *, latitude: float, longitude: float, locality_id: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"No neighborhood found for coordinates ({latitude}, {longitude})",
            code="NEIGHBORHOOD_RESOLUTION_NOT_FOUND",
            context={"latitude": latitude, "longitude": longitude, "locality_id": locality_id, **(context or {})},
        )
