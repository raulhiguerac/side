import uuid

from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import (
    account_cache_key,
    interests_cache_key,
    profile_cache_key,
)


async def invalidate_current_user_cache(cache: CachePort, account_id: uuid.UUID) -> None:
    try:
        await cache.delete(profile_cache_key(account_id))
        await cache.delete(account_cache_key(account_id))
        await cache.delete(interests_cache_key(account_id))
    except Exception:
        pass
