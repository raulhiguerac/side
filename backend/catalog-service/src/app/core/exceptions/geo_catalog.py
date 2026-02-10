import uuid
from typing import Any, Dict, Optional
from app.core.exceptions.base import BaseError

class LocalityNotFoundError(BaseError):
    def __init__(self, *, locality_id: uuid.UUID, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Locality '{locality_id}' not found",
            code="LOCALITY_NOT_FOUND",
            cause=cause,
            context={"locality_id": str(locality_id), **(context or {})},
        )

class NeighborhoodNotFoundError(BaseError):
    def __init__(self, *, neighborhood_id: uuid.UUID, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Neighborhood '{neighborhood_id}' not found",
            code="NEIGHBORHOOD_NOT_FOUND",
            cause=cause,
            context={"neighborhood_id": str(neighborhood_id), **(context or {})},
        )
