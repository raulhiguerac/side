from typing import Protocol, TypedDict


class EmailRecipient(TypedDict, total=False):
    email: str
    name: str

class EmailSenderPort(Protocol):
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
        ...

    async def send_template_email(
        self,
        *,
        template_id: int,
        to: list[EmailRecipient],
        params: dict[str, object] | None,
        sender: str | None = None,
        subject: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        ...