from typing import Any, Optional

from app.core.exceptions.base import BaseError


class CreatePropertyError(BaseError):
    def __init__(
        self,
        *,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message="Error while creating property",
            code="CREATE_PROPERTY_ERROR",
            cause=cause,
            context=context,
        )


class PropertyDbUnavailableError(BaseError):
    def __init__(self, *, cause: Optional[Exception] = None):
        super().__init__(
            message="Property database is unavailable",
            code="PROPERTY_DB_UNAVAILABLE",
            cause=cause,
        )


class InvalidLocationError(BaseError):
    def __init__(self, *, neighborhood_id: Any = None, cause: Optional[Exception] = None):
        super().__init__(
            message="The provided location is invalid or does not exist",
            code="INVALID_LOCATION",
            cause=cause,
            context={"neighborhood_id": str(neighborhood_id)} if neighborhood_id else {},
        )


class InconsistentLocationError(BaseError):
    def __init__(self, *, neighborhood_id: Any = None, city_id: Any = None):
        super().__init__(
            message="The neighborhood does not belong to the provided city",
            code="INCONSISTENT_LOCATION",
            context={
                "neighborhood_id": str(neighborhood_id),
                "city_id": str(city_id),
            },
        )


class CatalogServiceUnavailableError(BaseError):
    def __init__(self, *, cause: Optional[Exception] = None):
        super().__init__(
            message="Catalog service is unavailable",
            code="CATALOG_SERVICE_UNAVAILABLE",
            cause=cause,
        )
