from app.core.exceptions.base import BaseError

class InvalidCredentialsError(BaseError):
    def __init__(self, *, cause: Exception | None = None):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
            status_code=401,
            cause=cause,
        )