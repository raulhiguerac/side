from app.core.exceptions.base import BaseError

class EmailAlreadyRegisteredError(BaseError):
    def __init__(self, *, email: str):
        super().__init__(
            message="Email already registered",
            code="EMAIL_ALREADY_REGISTERED",
            status_code=409,
            context={"email": email},
        )