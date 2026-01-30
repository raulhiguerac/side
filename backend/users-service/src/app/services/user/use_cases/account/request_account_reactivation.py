import secrets

from app.core.config.settings import settings

from app.services.user.helpers.cache_keys import reactivation_cache_key
from app.services.shared.helpers.security import hash_token
from app.services.shared.helpers.url_builder import build_redirect_url

from app.services.user.services.get_profile_orchestrator import ProfileApplicationService
from app.services.user.services.reactivation_mailer import ReactivationMailer
from app.services.shared.ports.cache import CachePort
from app.services.user.ports.unit_of_work import UserUnitOfWork

from app.models.account import AccountActionActor, AccountType
from app.core.exceptions.account import AccountNotFoundError

class RequestReactivationUseCase:
    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
        profile_service: ProfileApplicationService,
        reactivation_mailer: ReactivationMailer,
    ) -> None:
        self.uow = uow
        self.cache = cache_client
        self.profile_service = profile_service
        self.reactivation_mailer = reactivation_mailer
    
    @staticmethod
    def _is_eligible_for_reactivation(account) -> bool:
        return (
            not account.is_active
            and account.deactivated_at is not None
            and account.deactivated_by == AccountActionActor.user
        )

    @staticmethod
    def _resolve_display_name(profile) -> str:
        match profile.account_type:
            case AccountType.person:
                return profile.first_name
            case AccountType.organization:
                return profile.display_name
            case _:
                return ""

    async def execute(self, *, email: str) -> None:
        normalized_email = email.lower().strip()

        try:
            account = await self.uow.accounts.get_by_email(email=normalized_email)
        except AccountNotFoundError:
            return

        if not self._is_eligible_for_reactivation(account):
            return

        token = secrets.token_urlsafe(32)
        token_hash = hash_token(token)
        cache_key = reactivation_cache_key(token_hash)

        await self.cache.set_json(
            key=cache_key,
            value={
                "account_id": str(account.account_id),
            },
            ttl=settings.CACHE_REACTIVATION_TTL_SECONDS,
        )

        redirect_url = build_redirect_url(
            front_base_url=settings.FRONT_BASE_URL,
            path="/reactivate",
            query_params={"token": token},
        )

        profile = await self.profile_service.get_profile(
            account_id=account.account_id,
        )
        display_name = self._resolve_display_name(profile.profile)

        await self.reactivation_mailer.send_reactivation_email(
            email=account.email,
            name=display_name,
            redirect_url=redirect_url,
        )
