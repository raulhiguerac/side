
from fastapi.concurrency import run_in_threadpool

from app.integrations.email.brevo.client import EmailClient
from app.services.shared.ports.email_sender import EmailRecipient, EmailSenderPort


class BrevoSenderAdapter(EmailSenderPort):
    def __init__(self, client: EmailClient) -> None:
        self._client = client

    async def send_email(
        self,
        *,
        sender: str,
        to: list[EmailRecipient],
        subject: str,
        html_content: str,
        text_content: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        return await run_in_threadpool(
            self._client.send_email,
            sender=sender,
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags=tags or [],
        )
    
    async def send_template_email(
        self,
        *,
        template_id: int,
        to: list[EmailRecipient],
        params: dict[str, object] | None = None,
        sender: str | None = None,
        subject: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        return await run_in_threadpool(
            self._client.send_email_template,
            template_id=template_id,
            to=to,
            params=params or {},
            sender=sender,
            subject=subject,
            tags=tags or [],
        )
