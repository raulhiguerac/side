from typing import Any

from app.core.exceptions.base import BaseError


class EmailSenderMisconfiguredError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: dict[str, Any] | None = None):
        super().__init__(
            message="Email provider is misconfigured",
            code="EMAIL_PROVIDER_MISCONFIGURED",
            cause=cause,
            context=context
        )

class EmailSenderUnavailableError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: dict[str, Any] | None = None):
        super().__init__(
            message="Email sender is unavailable",
            code="EMAIL_SENDER_UNAVAILABLE",
            cause=cause,
            context=context
        )

class SmtpMisconfiguredError(BaseError):
    def __init__(self, *, cause: Exception | None = None, context: dict[str, Any] | None = None):
        super().__init__(
            message="SMTP is misconfigured",
            code="SMTP_MISCONFIGURED",
            cause=cause,
            context=context
        )
