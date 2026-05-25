from app.core.exceptions.base import BaseError


class UnauthorizedError(BaseError):
    def __init__(self, *, detail: str | None = None, cause: Exception | None = None) -> None:
        super().__init__(
            message="Missing or invalid token",
            code="UNAUTHORIZED",
            context={"detail": detail} if detail else {},
            cause=cause,
            http_status=401,
        )


class ForbiddenError(BaseError):
    def __init__(self) -> None:
        super().__init__(
            message="Insufficient permissions",
            code="FORBIDDEN",
            http_status=403,
        )
