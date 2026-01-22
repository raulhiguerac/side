from app.services.shared.ports.email_sender import EmailSenderPort


RESET_PASSWORD_TEMPLATE_ID = 2


class ResetPasswordMailer:
    def __init__(self, email_sender: EmailSenderPort) -> None:
        self._email_sender = email_sender

    async def send(
        self,
        *,
        email: str,
        name: str,
        redirect_url: str,
    ) -> None:
        await self._email_sender.send_template_email(
            template_id=RESET_PASSWORD_TEMPLATE_ID,
            to=[{"email": email}],
            params={
                "name": name,
                "redirect_url": redirect_url,
            },
            tags=["reset-password"],
        )
