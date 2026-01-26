import secrets

from app.core.config.settings import settings
from app.services.shared.helpers.security import hash_token
from app.services.shared.helpers.url_builder import build_redirect_url
from app.services.user.helpers.cache_keys import reset_password_cache_key
from app.services.shared.ports.cache import CachePort

from app.services.auth.ports.unit_of_work import AuthUnitOfWork
from app.services.auth.services.reset_password_mailer import ResetPasswordMailer


class RequestResetPasswordUseCase:
    def __init__(
        self,
        *,
        uow: AuthUnitOfWork,
        cache_client: CachePort,
        reset_password_mailer: ResetPasswordMailer,
    ) -> None:
        self.uow = uow
        self.cache = cache_client
        self.reset_password_mailer = reset_password_mailer

    async def execute(self, *, email: str) -> None:
        normalized_email = email.lower().strip()

        account = await self.uow.accounts.get_by_email(
            email=normalized_email
        )

        if not account or not account.is_active:
            return

        token = secrets.token_urlsafe(32)
        cache_key = reset_password_cache_key(hash_token(token))

        await self.cache.set_json(
            key=cache_key,
            value={"account_id": str(account.account_id)},
            ttl=settings.CACHE_REACTIVATION_TTL_SECONDS,  # split reset TTL
        )

        redirect_url = build_redirect_url(
            front_base_url=settings.FRONT_BASE_URL,
            path="/reset-password",
            query_params={"token": token},
        )

        display_name = (
            await self.uow.email_recipients.get_display_name_by_account_id(
                account_id=account.account_id,
                account_type=account.account_type,
            )
        ) or ""

        await self.reset_password_mailer.send_reset_password_email(
            email=normalized_email,
            name=display_name,
            redirect_url=redirect_url,
        )