from datetime import datetime

from app.schemas.common import Principal
from app.models.account import AccountActionActor, AccountDeactivationReason
from app.services.user.helpers.cache_keys import account_cache_key, profile_cache_key
from app.services.shared.ports.cache import CachePort
from app.services.user.ports.unit_of_work import UserUnitOfWork


class DeactivateCurrentAccountUseCase:
    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def execute(self, *, principal: Principal) -> None:
        account_id = principal.sub
        account = await self.uow.accounts.get_by_id(account_id=account_id)

        if not account.is_active:
            return

        account.is_active = False
        account.deactivated_at = datetime.utcnow()
        account.deactivated_by = AccountActionActor.user
        account.deactivation_reason = AccountDeactivationReason.user_request

        try:
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

        try:
            await self.cache.delete(key=account_cache_key(account_id))
            await self.cache.delete(key=profile_cache_key(account_id))
        except Exception:
            pass
