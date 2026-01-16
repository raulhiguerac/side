import os
import uuid

from typing import Optional
from pydantic import ValidationError

from app.models.account import AccountType

from app.schemas.user import CurrentUserProfileOut
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.ports.cache import CachePort

from app.services.user.helpers.profile_helpers import profile_cache_key, get_profile_db
from app.services.user.mapper import map_profile_db_to_schema


PROFILE_CACHE_TTL_SECONDS = int(os.getenv("PROFILE_CACHE_TTL_SECONDS", "600"))


class CurrentProfileReader:
    """
    Cache-aside reader for the current user's profile.

    Flow:
    1) Resolve current account context (via CurrentAccountReader)
    2) Try cache (CurrentUserProfileOut)
    3) On miss → load from DB
    4) Map to schema
    5) Populate cache
    """

    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache = cache_client

    async def get_from_cache(self, *, account_id: uuid.UUID) -> Optional[CurrentUserProfileOut]:
        profile_key = profile_cache_key(account_id)
        cached = await self.cache.get(key=profile_key)
        if cached:
            try:
                return CurrentUserProfileOut.model_validate_json(cached)
            except ValidationError:
                return None
        return None

    async def get(self, *, account_id: uuid.UUID, account_type: AccountType) -> CurrentUserProfileOut:
        profile_key = profile_cache_key(account_id)

        profile_db = await get_profile_db(
            uow=self.uow,
            account_id=account_id,
            account_type=account_type,
        )

        profile_model = map_profile_db_to_schema(account_type, profile_db)
        out = CurrentUserProfileOut(profile=profile_model)

        await self.cache.set(
            key=profile_key,
            value=out.model_dump_json(),
            ttl=PROFILE_CACHE_TTL_SECONDS,
        )

        return out