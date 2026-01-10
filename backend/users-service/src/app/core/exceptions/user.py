import uuid
from typing import Optional
from app.core.exceptions.base import BaseError

class AccountNotFoundError(BaseError):
    def __init__(self, *, account_id: Optional[uuid.UUID] = None, email: Optional[str] = None):
        if account_id:
            context = {"account_id": str(account_id)}
        if email:
            context["email"] = email

        super().__init__(
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            context=context,
        )

class AccountDisabledError(BaseError):
    def __init__(self, *, account_id: Optional[uuid.UUID] = None, email: Optional[str] = None):
        if account_id:
            context = {"account_id": str(account_id)}
        if email:
            context["email"] = email

        super().__init__(
            message="Account disabled",
            code="ACCOUNT_DISABLED",
            context=context,
        )

class ProfileNotFoundError(BaseError):
    def __init__(self, *, account_id: Optional[uuid.UUID] = None):
        if account_id:
            context = {"account_id": str(account_id)}

        super().__init__(
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            context=context,
        )