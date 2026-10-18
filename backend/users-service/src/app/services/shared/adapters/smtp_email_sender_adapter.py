from email.message import EmailMessage

import aiosmtplib

from app.core.exceptions.email import (
    EmailSenderUnavailableError,
    SmtpMisconfiguredError,
)
from app.services.shared.ports.email_sender import EmailSenderPort


class SmtpEmailSenderAdapter(EmailSenderPort):
    def __init__(self, *, host: str, port: int, username: str, password: str, sender: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender

    async def send_email(self, *, to: list[str], subject: str, html_content: str, text_content: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = ", ".join(to)
        message["Subject"] = subject
        message.set_content(text_content)
        message.add_alternative(html_content, subtype="html")

        try:
            await aiosmtplib.send(
                message,
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                use_tls=self._port == 465,  # 587 negocia STARTTLS solo
            )
        except aiosmtplib.SMTPAuthenticationError as e:
            raise SmtpMisconfiguredError(
                cause=e,
                context={"provider": "smtp", "code": e.code, "reason": e.message},
            ) from e
        except aiosmtplib.SMTPException as e:
            raise EmailSenderUnavailableError(
                cause=e,
                context={"provider": "smtp", "host": self._host, "reason": str(e)},
            ) from e
