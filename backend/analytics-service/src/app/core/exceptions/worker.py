from app.core.exceptions.base import BaseError


class WorkerConfigurationError(BaseError):
    def __init__(self, *, missing: list[str]) -> None:
        super().__init__(
            message=f"Missing required worker env vars: {', '.join(missing)}",
            code="WORKER_CONFIGURATION_ERROR",
            context={"missing": missing},
            http_status=500,
        )
