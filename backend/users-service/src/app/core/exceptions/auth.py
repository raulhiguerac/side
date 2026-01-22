from app.core.exceptions.base import BaseError

class EmailAlreadyRegisteredError(BaseError):
    def __init__(self, *, email: str):
        super().__init__(
            message="Email already registered",
            code="EMAIL_ALREADY_REGISTERED",
            context={"email": email},
        )

class InvalidCredentialsError(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
            cause=cause,
        )

class InvalidRefreshTokenError(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Invalid refresh token",
            code="INVALID_REFRESH_TOKEN",
            cause=cause,
        )

class MissingCookieException(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Authentication token missing in cookies",
            code="MISSING_TOKEN",
            cause=cause,
        )

class InvalidTokenException(BaseError):
    def __init__(self, *, detail: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="Invalid authentication token",
            code="INVALID_TOKEN",
            context={"detail": detail},
            cause=cause,
        )

class SamePasswordNotAllowedError(BaseError):
    def __init__(self, *, detail: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="New password is equal to the old password",
            code="PASSWORD_SAME_AS_OLD",
            context={"detail": detail},
            cause=cause,
        )

class TokenInvalidOrExpiredError(BaseError):
    def __init__(self, *, detail: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="The token is invalid or expired",
            code="TOKEN_INVALID_OR_EXPIRED",
            context={"detail": detail},
            cause=cause,
        )