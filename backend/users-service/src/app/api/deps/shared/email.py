import os
from functools import lru_cache

from app.core.exceptions.email import SmtpMisconfiguredError
from app.services.shared.adapters.smtp_email_sender_adapter import (
    SmtpEmailSenderAdapter,
)
from app.services.shared.ports.email_sender import EmailSenderPort

SMTP_REQUIRED_ENV = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")


@lru_cache(maxsize=1)
def get_email_sender() -> EmailSenderPort:
    missing = [name for name in SMTP_REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise SmtpMisconfiguredError(context={"missing": missing})

    try:
        port = int(os.environ["SMTP_PORT"])
    except ValueError as e:
        raise SmtpMisconfiguredError(cause=e, context={"invalid": "SMTP_PORT"}) from e

    return SmtpEmailSenderAdapter(
        host=os.environ["SMTP_HOST"],
        port=port,
        username=os.environ["SMTP_USERNAME"],
        password=os.environ["SMTP_PASSWORD"],
        sender=os.environ["SMTP_FROM"],
    )
