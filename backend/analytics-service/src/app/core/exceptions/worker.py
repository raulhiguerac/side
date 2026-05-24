from app.core.exceptions.base import BaseError


class WorkerConfigurationError(BaseError):
    def __init__(self, *, missing: list[str]) -> None:
        super().__init__(
            message=f"Missing required worker env vars: {', '.join(missing)}",
            code="WORKER_CONFIGURATION_ERROR",
            context={"missing": missing},
            http_status=500,
        )


class WorkerDeliveryError(BaseError):
    def __init__(self, *, topic: str, errors: list[str], pending: int = 0) -> None:
        super().__init__(
            message=f"Failed to deliver worker messages to topic {topic}",
            code="WORKER_DELIVERY_ERROR",
            context={"topic": topic, "errors": errors, "pending": pending},
            http_status=500,
        )
