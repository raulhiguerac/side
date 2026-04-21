from typing import Any, Optional

from app.core.exceptions.base import BaseError


class PromotionNotFoundError(BaseError):
    def __init__(self, *, property_id: Any = None):
        super().__init__(
            message="No active promotion found for this property",
            code="PROMOTION_NOT_FOUND",
            context={"property_id": str(property_id)} if property_id else {},
        )


class PropertyNotReadyForPromotionError(BaseError):
    def __init__(self, *, property_id: Any = None):
        super().__init__(
            message="Property must be active before it can be promoted",
            code="PROPERTY_NOT_READY_FOR_PROMOTION",
            http_status=409,
            context={"property_id": str(property_id)} if property_id else {},
        )


class DuplicateActivePromotionError(BaseError):
    def __init__(self, *, property_id: Any = None):
        super().__init__(
            message="Property already has an active promotion",
            code="DUPLICATE_ACTIVE_PROMOTION",
            http_status=409,
            context={"property_id": str(property_id)} if property_id else {},
        )


class PromotionError(BaseError):
    def __init__(
        self,
        *,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message="Error while creating promotion",
            code="PROMOTION_ERROR",
            cause=cause,
            context=context,
        )


class SetEstimatedPriceError(BaseError):
    def __init__(
        self,
        *,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message="Error while setting estimated price",
            code="SET_ESTIMATED_PRICE_ERROR",
            cause=cause,
            context=context,
        )


class SetVisibilityError(BaseError):
    def __init__(
        self,
        *,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message="Error while updating property visibility",
            code="SET_VISIBILITY_ERROR",
            cause=cause,
            context=context,
        )


class DeletePropertyError(BaseError):
    def __init__(
        self,
        *,
        cause: Optional[Exception] = None,
        context: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            message="Error while deleting property",
            code="DELETE_PROPERTY_ERROR",
            cause=cause,
            context=context,
        )


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


class LocationNotResolvedError(BaseError):
    def __init__(self, *, lat: float, lon: float):
        super().__init__(
            message="No neighborhood found for the provided coordinates",
            code="LOCATION_NOT_RESOLVED",
            context={"lat": lat, "lon": lon},
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


class PropertyForbiddenError(BaseError):
    def __init__(self, *, property_id: Any = None):
        super().__init__(
            message="You do not have permission to modify this property",
            code="PROPERTY_FORBIDDEN",
            context={"property_id": str(property_id)} if property_id else {},
        )


class InvalidStatusTransitionError(BaseError):
    def __init__(self, *, current: str, target: str):
        super().__init__(
            message=f"Cannot transition property from '{current}' to '{target}'",
            code="INVALID_STATUS_TRANSITION",
            context={"current": current, "target": target},
        )


class PropertyNotFoundError(BaseError):
    def __init__(self, *, property_id: Any = None):
        super().__init__(
            message="Property not found",
            code="PROPERTY_NOT_FOUND",
            context={"property_id": str(property_id)} if property_id else {},
        )


class CatalogServiceUnavailableError(BaseError):
    def __init__(self, *, cause: Optional[Exception] = None):
        super().__init__(
            message="Catalog service is unavailable",
            code="CATALOG_SERVICE_UNAVAILABLE",
            cause=cause,
        )


class ImageCountExceededError(BaseError):
    def __init__(self, *, max: int, requested: int):
        super().__init__(
            message=f"Requested {requested} images but maximum allowed is {max}",
            code="IMAGE_COUNT_EXCEEDED",
            http_status=400,
            context={"max": max, "requested": requested},
        )


class ImageNotOwnedError(BaseError):
    def __init__(self, *, image_ids: list):
        super().__init__(
            message="One or more images do not belong to this property",
            code="IMAGE_NOT_OWNED",
            context={"image_ids": [str(i) for i in image_ids]},
        )


class BatchNotFoundError(BaseError):
    def __init__(self, *, batch_id: Any = None):
        super().__init__(
            message="Upload batch not found",
            code="BATCH_NOT_FOUND",
            context={"batch_id": str(batch_id)} if batch_id else {},
        )


class BatchExpiredError(BaseError):
    def __init__(self, *, batch_id: Any = None):
        super().__init__(
            message="Upload batch has expired",
            code="BATCH_EXPIRED",
            context={"batch_id": str(batch_id)} if batch_id else {},
        )


class BatchInvalidStateError(BaseError):
    def __init__(self, *, batch_id: Any = None, status: str = ""):
        super().__init__(
            message=f"Upload batch cannot be confirmed in state '{status}'",
            code="BATCH_INVALID_STATE",
            context={"batch_id": str(batch_id) if batch_id else None, "status": status},
        )


class BatchNotConsistentError(BaseError):
    def __init__(self, *, batch_id: Any = None, expected: int = 0, got: int = 0):
        super().__init__(
            message="Batch key count does not match the requested create count",
            code="BATCH_NOT_CONSISTENT",
            context={"batch_id": str(batch_id) if batch_id else None, "expected": expected, "got": got},
        )
