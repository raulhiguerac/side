from typing import Dict, List, Optional, Protocol, TypedDict


class EmailRecipient(TypedDict, total=False):
    email: str
    name: str

class EmailSenderPort(Protocol):
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
        ...

    async def send_template_email(
        self,
        *,
        template_id: int,
        to: List[EmailRecipient],
        params: Optional[Dict[str, object]],
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        ...