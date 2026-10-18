from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from app.core.config.settings import settings
from app.services.shared.ports.email_sender import EmailSenderPort

REACTIVATION_SUBJECT = "Reactiva tu cuenta de Mi Casa en Minutos"


class ReactivationMailer:
    def __init__(self, email_sender: EmailSenderPort):
        self._email_sender = email_sender
        self._env = Environment(
            loader=PackageLoader("app", "templates/email"),
            autoescape=select_autoescape(["html"]),
            undefined=StrictUndefined,
        )

    async def send_reactivation_email(self, email: str, name: str, redirect_url: str) -> None:
        context = {
            "name": name,
            "email": email,
            "redirect_url": redirect_url,
            "ttl_minutes": settings.CACHE_REACTIVATION_TTL_SECONDS // 60,
        }

        await self._email_sender.send_email(
            to=[email],
            subject=REACTIVATION_SUBJECT,
            html_content=self._env.get_template("reactivation.html").render(context),
            text_content=self._env.get_template("reactivation.txt").render(context),
        )
