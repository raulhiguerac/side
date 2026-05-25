from typing import Any, Optional

from app.core.exceptions.base import BaseError


class PredictionPersistenceError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: Optional[dict[str, Any]] = None):
        super().__init__(
            message="Failed to persist prediction",
            code="PREDICTION_PERSISTENCE_ERROR",
            cause=cause,
            context=context or {},
            http_status=500,
        )
