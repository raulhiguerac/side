import uuid
from typing import Any, Dict, Optional

from app.core.exceptions.base import BaseError


class CatalogAdminDbUnavailableError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Database is unavailable or timed out",
            code="CATALOG_ADMIN_DB_UNAVAILABLE",
            cause=cause,
            context=context,
        )


class CountryNotFoundError(BaseError):
    def __init__(self, *, country_id: uuid.UUID):
        super().__init__(
            message=f"Country '{country_id}' not found",
            code="COUNTRY_NOT_FOUND",
            context={"country_id": str(country_id)},
        )


class CountryConflictError(BaseError):
    def __init__(self, *, field: str, value: str):
        super().__init__(
            message=f"Country with {field} '{value}' already exists",
            code="COUNTRY_CONFLICT",
            context={"field": field, "value": value},
        )


class AdminDivisionNotFoundError(BaseError):
    def __init__(self, *, admin_division_id: uuid.UUID):
        super().__init__(
            message=f"AdminDivision '{admin_division_id}' not found",
            code="ADMIN_DIVISION_NOT_FOUND",
            context={"admin_division_id": str(admin_division_id)},
        )


class AdminDivisionConflictError(BaseError):
    def __init__(self, *, field: str, value: str):
        super().__init__(
            message=f"AdminDivision with {field} '{value}' already exists",
            code="ADMIN_DIVISION_CONFLICT",
            context={"field": field, "value": value},
        )


class LocalityAdminNotFoundError(BaseError):
    def __init__(self, *, locality_id: uuid.UUID):
        super().__init__(
            message=f"Locality '{locality_id}' not found",
            code="LOCALITY_ADMIN_NOT_FOUND",
            context={"locality_id": str(locality_id)},
        )


class LocalityConflictError(BaseError):
    def __init__(self, *, field: str, value: str):
        super().__init__(
            message=f"Locality with {field} '{value}' already exists",
            code="LOCALITY_CONFLICT",
            context={"field": field, "value": value},
        )


class NeighborhoodAdminNotFoundError(BaseError):
    def __init__(self, *, neighborhood_id: uuid.UUID):
        super().__init__(
            message=f"Neighborhood '{neighborhood_id}' not found",
            code="NEIGHBORHOOD_ADMIN_NOT_FOUND",
            context={"neighborhood_id": str(neighborhood_id)},
        )


class NeighborhoodConflictError(BaseError):
    def __init__(self, *, field: str, value: str):
        super().__init__(
            message=f"Neighborhood with {field} '{value}' already exists",
            code="NEIGHBORHOOD_CONFLICT",
            context={"field": field, "value": value},
        )
