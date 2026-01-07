from app.core.exceptions.base import BaseError

class InvalidCredentialsError(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
            status_code=401,
            cause=cause,
        )

class MissingCookieException(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Authentication token missing in cookies",
            code="MISSING_TOKEN",
            status_code=401,
            cause=cause,
        )

class InvalidTokenException(BaseError):
    def __init__(self, *, detail: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="Invalid authentication token",
            code="INVALID_TOKEN",
            status_code=401,
            context={"detail": detail},
            cause=cause,
        )