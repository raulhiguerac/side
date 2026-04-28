import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.search.ports.unit_of_work import SearchUnitOfWork
from app.services.search.schemas.feed_schemas import FeedPreferences
from app.services.shared.helpers.cache_keys import feed_ads_by_city, feed_ads_global
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema

_ADS_CACHE_TTL = 3600  # 1 hour


async def get_ads(
    *,
    preferences: FeedPreferences | None,
    uow: SearchUnitOfWork,
    cache: CachePort,
) -> list[PropertyCardSchema]:
    ads: list[PropertyCardSchema] = []
    missing_city_ids: list[uuid.UUID] = []

    if not preferences:
        cached = await _read_cache(cache, feed_ads_global())
        if cached:
            return cached
        return await _fetch_and_cache_ads(uow=uow, cache=cache, city_ids=None)

    for city_id in preferences.city_ids:
        cached = await _read_cache(cache, feed_ads_by_city(city_id))
        if cached:
            ads.extend(cached)
        else:
            missing_city_ids.append(city_id)

    if missing_city_ids:
        fetched = await _fetch_and_cache_ads(uow=uow, cache=cache, city_ids=missing_city_ids)
        ads.extend(fetched)

    return ads


async def _fetch_and_cache_ads(
    *,
    uow: SearchUnitOfWork,
    cache: CachePort,
    city_ids: list[uuid.UUID] | None,
) -> list[PropertyCardSchema]:
    raw = await run_in_threadpool(
        partial(
            uow.properties.get_properties,
            city_ids=city_ids,
            promoted_only=True,
        )
    )

    if not raw:
        return []

    if city_ids is None:
        ads = [PropertyCardSchema.model_validate(p) for p in raw]
        try:
            await cache.set_json(
                key=feed_ads_global(),
                value=[a.model_dump(mode="json") for a in ads],
                ttl=_ADS_CACHE_TTL,
            )
        except Exception:
            pass
        return ads

    ads: list[PropertyCardSchema] = []
    for city_id in city_ids:
        city_ads = [
            PropertyCardSchema.model_validate(p)
            for p in raw
            if p.location and p.location.city_id == city_id
        ]
        if city_ads:
            try:
                await cache.set_json(
                    key=feed_ads_by_city(city_id),
                    value=[a.model_dump(mode="json") for a in city_ads],
                    ttl=_ADS_CACHE_TTL,
                )
            except Exception:
                pass
            ads.extend(city_ads)

    return ads


async def _read_cache(cache: CachePort, key: str) -> list[PropertyCardSchema] | None:
    try:
        cached = await cache.get_json(key=key)
        if cached:
            return [PropertyCardSchema.model_validate(a) for a in cached]
    except Exception:
        pass
    return None
