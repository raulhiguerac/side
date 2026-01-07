import uuid
from typing import Optional
from app.core.exceptions.base import BaseError

class EmailAlreadyRegisteredError(BaseError):
    def __init__(self, *, email: str):
        super().__init__(
            message="Email already registered",
            code="EMAIL_ALREADY_REGISTERED",
            status_code=409,
            context={"email": email},
        )

class AccountNotFoundError(BaseError):
    def __init__(self, *, account_id: uuid.UUID, email: Optional[str] = None):
        context = {"account_id": str(account_id)}
        if email:
            context["email"] = email

        super().__init__(
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            status_code=404,
            context=context,
        )