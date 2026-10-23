from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from app.core.config.settings import settings
from app.services.shared.ports.email_sender import EmailSenderPort

RESET_PASSWORD_SUBJECT = "Restablece tu contraseña de Mi Casa en Minutos"


class ResetPasswordMailer:
    def __init__(self, email_sender: EmailSenderPort) -> None:
        self._email_sender = email_sender
        self._env = Environment(
            loader=PackageLoader("app", "templates/email"),
            autoescape=select_autoescape(["html"]),
            undefined=StrictUndefined,
        )

    async def send_reset_password_email(self, *, email: str, name: str, redirect_url: str) -> None:
        context = {
            "name": name,
            "redirect_url": redirect_url,
            "ttl_minutes": settings.CACHE_REACTIVATION_TTL_SECONDS // 60,
        }

        await self._email_sender.send_email(
            to=[email],
            subject=RESET_PASSWORD_SUBJECT,
            html_content=self._env.get_template("reset_password.html").render(context),
            text_content=self._env.get_template("reset_password.txt").render(context),
        )
