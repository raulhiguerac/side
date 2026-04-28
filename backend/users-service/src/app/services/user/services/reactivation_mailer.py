from app.services.shared.ports.email_sender import EmailSenderPort

class ReactivationMailer:
    def __init__(self, email_sender: EmailSenderPort):
        self._email_sender = email_sender

    async def send_reactivation_email(self, email: str, name: str, redirect_url: str) -> None:
        await self._email_sender.send_template_email(
            template_id=1,
            to=[{"email":email}],
            params={
                "name":name,
                "email":email,
                "redirect_url":redirect_url
            },
            tags=["reactivation"]
        )
