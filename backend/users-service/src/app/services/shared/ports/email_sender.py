from typing import Protocol


class EmailSenderPort(Protocol):
    async def send_email(
        self,
        *,
        to: list[str],
        subject: str,
        html_content: str,
        text_content: str,
    ) -> None:
        ...
