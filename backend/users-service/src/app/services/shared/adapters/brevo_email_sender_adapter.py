from typing import Dict, List, Optional

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
        to: List[EmailRecipient],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        tags: Optional[List[str]] = None,
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
        to: List[EmailRecipient],
        params: Optional[Dict[str, object]] = None,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        tags: Optional[List[str]] = None,
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
