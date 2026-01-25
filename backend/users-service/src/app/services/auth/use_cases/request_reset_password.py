import secrets

from app.core.config.settings import settings

from app.services.shared.helpers.security import hash_token
from app.services.shared.helpers.url_builder import build_redirect_url
from app.services.user.helpers.cache_keys import reset_password_cache_key

from app.services.shared.ports.cache import CachePort

from app.services.shared.policies.active_account_policy import AccountActivePolicy
from app.services.auth.services.reset_password_mailer import ResetPasswordMailer

from app.core.exceptions.auth import InvalidCredentialsError
class RequestResetPasswordUseCase:
    def __init__(
        self,
        *,
        cache_client: CachePort,
        account_guard: AccountActivePolicy,
        reset_password_mailer: ResetPasswordMailer,
    ) -> None:
        self.cache = cache_client
        self.account_guard = account_guard
        self.reset_password_mailer = reset_password_mailer

    async def execute(self, *, email: str) -> None:
        normalized_email = email.lower().strip()
        try:
            account = await self.account_guard.ensure_active_by_email(email=normalized_email)
        except InvalidCredentialsError:
            return

        token = secrets.token_urlsafe(32)
        token_hash = hash_token(token)
        cache_key = reset_password_cache_key(token_hash)

        await self.cache.set_json(
            key=cache_key,
            value={
                "account_id": str(account.account_id),
            },
            ttl=settings.CACHE_REACTIVATION_TTL_SECONDS,
        )

        redirect_url = build_redirect_url(
            front_base_url=settings.FRONT_BASE_URL,
            path="/reset-password",
            query_params={"token": token},
        )
        
        await self.reset_password_mailer.send(
            email=email,
            name="",
            redirect_url=redirect_url,
        )