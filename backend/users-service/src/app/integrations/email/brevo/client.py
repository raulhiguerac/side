import os
from typing import Dict, List, Optional

import brevo_python
from brevo_python.rest import ApiException

from app.core.exceptions.email import (
    EmailSenderMisconfiguredError,
    EmailSenderUnavailableError,
)


class EmailClient:
    def __init__(self) -> None:
        api_key = os.getenv("BREVO_API_KEY")
        if not api_key:
            raise EmailSenderMisconfiguredError(
                context={"missing": "BREVO_API_KEY"}
            )

        configuration = brevo_python.Configuration()
        configuration.api_key["api-key"] = api_key

        api_client = brevo_python.ApiClient(configuration)
        self._emails_api = brevo_python.TransactionalEmailsApi(api_client)

    def send_email(
        self,
        *,
        sender: str,
        to: List[Dict[str, str]],
        subject: str,
        html_content: str,
        tags: Optional[List[str]] = None,
    ) -> None:
        email = brevo_python.SendSmtpEmail(
            sender={"email": sender},
            to=to,
            subject=subject,
            html_content=html_content,
            tags=tags or [],
        )

        try:
            self._emails_api.send_transac_email(email)
        except ApiException as e:
            raise EmailSenderUnavailableError(
                cause=e,
                context={
                    "provider": "brevo",
                    "status": getattr(e, "status", None),
                    "reason": getattr(e, "reason", None),
                },
            )
    
    def send_email_template(
        self,
        *,
        template_id: int,
        to: List[Dict[str, str]],
        params: Optional[Dict[str, object]] = None,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        email = brevo_python.SendSmtpEmail(
            to=to,
            template_id=template_id,
            params=params or {},
            tags=tags or [],
            # sender={"email": sender} if sender else None,
            subject=subject,
        )
        
        try:
            self._emails_api.send_transac_email(email)
        except ApiException as e:
            print(str(e))
            raise EmailSenderUnavailableError(
                cause=e,
                context={
                    "provider": "brevo",
                    "status": getattr(e, "status", None),
                    "reason": getattr(e, "reason", None),
                },
            )