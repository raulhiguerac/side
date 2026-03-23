import uuid

from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import interests_cache_key
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.schemas.current import UserInterestsResponse


class GetUserInterestsUseCase:
    def __init__(self, *, uow: UserUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, account_id: uuid.UUID) -> UserInterestsResponse:
        cached = await self.cache.get_json(key=interests_cache_key(account_id))
        if cached:
            return UserInterestsResponse.model_validate(cached)

        result = await self.uow.accounts.get_interests(account_id=account_id)

        if result.localities:
            try:
                await self.cache.set_json(
                    key=interests_cache_key(account_id),
                    value=result.model_dump(mode="json"),
                    ttl=86400,
                )
            except Exception:
                pass

        return result
