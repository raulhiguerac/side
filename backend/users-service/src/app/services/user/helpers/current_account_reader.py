import os
import uuid

from pydantic import ValidationError

from app.core.exceptions.user import AccountDisabledError
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import account_cache_key
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.schemas.current import CurrentUserOut

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "120"))


class CurrentAccountReader:
    """
    Cache-aside reader for the current account.

    Responsibilities:
    - Read CurrentUserOut from cache
    - Load Account from DB on cache miss
    - Validate invariants (exists, is_active)
    - Populate cache
    """

    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def get(self, *, account_id: uuid.UUID) -> CurrentUserOut:
        cache_key = account_cache_key(account_id)

        cached = await self.cache.get(key=cache_key)
        if cached:
            try:
                return CurrentUserOut.model_validate_json(cached)
            except ValidationError:
                pass

        account = await self.uow.accounts.get_by_id(account_id=account_id)

        model = CurrentUserOut.model_validate(account)

        await self.cache.set(
            key=cache_key,
            value=model.model_dump_json(),
            ttl=CACHE_TTL_SECONDS,
        )

        return model
    
    async def get_active(self, *, account_id: uuid.UUID) -> CurrentUserOut:
        account = await self.get(account_id=account_id)

        if not account.is_active:
            raise AccountDisabledError(
                account_id=account_id,
                email=account.email,
            )

        return account
