import uuid

from app.core.exceptions.base import BaseError


class AccountNotFoundError(BaseError):
    def __init__(self, *, account_id: uuid.UUID | None = None, email: str | None = None):
        context: dict[str, str] = {}
        if account_id:
            context = {"account_id": str(account_id)}
        if email:
            context["email"] = email

        super().__init__(
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            context=context,
        )