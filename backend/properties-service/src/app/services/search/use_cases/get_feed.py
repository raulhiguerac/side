from typing import Optional

from app.core.config.settings import settings
from app.services.search.helpers.feed.ads import get_ads
from app.services.search.helpers.feed.organic import get_organic
from app.services.search.ports.unit_of_work import SearchUnitOfWork
from app.services.search.schemas.feed_schemas import FeedCursor, FeedFilters, FeedPreferences, FeedPage
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema

from app.services.search.helpers.feed.encoding import encode_cursor, decode_cursor
from app.services.shared.helpers.cache_keys import feed_page

class GetFeedUseCase:
    def __init__(self, *, uow: SearchUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        *,
        preferences: Optional[FeedPreferences],
        filters: Optional[FeedFilters],
        cursor_str: Optional[str],
    ) -> FeedPage:
        
        cursor = None
        if cursor_str:
            cursor = decode_cursor(cursor_str)
            if cursor.position >= settings.FEED_MAX_RESULTS:
                return FeedPage(items=[], next_cursor=None)

        cache_key = feed_page(
            cursor_str,
            preferences=preferences.model_dump(mode="json") if preferences else None,
            filters=filters.model_dump(mode="json") if filters else None,
        )
        cached = await self.cache.get_json(key=cache_key)
        if cached:
            organic_items = [PropertyCardSchema.model_validate(item) for item in cached["items"]]
            ads = await get_ads(preferences=preferences, uow=self.uow, cache=self.cache)
            if not ads:
                return FeedPage(items=organic_items, next_cursor=cached["next_cursor"])
            new_position = cursor.position if cursor else 0
            ad_start = (new_position // settings.FEED_AD_INTERVAL) % len(ads)
            return FeedPage(
                items=self._inject_ads(organic=organic_items, ads=ads, ad_interval=settings.FEED_AD_INTERVAL, ad_start=ad_start),
                next_cursor=cached["next_cursor"],
            )

        page_size = settings.FEED_PAGE_SIZE
        ad_interval = settings.FEED_AD_INTERVAL

        ads = await get_ads(preferences=preferences, uow=self.uow, cache=self.cache)

        ads_per_page = min(len(ads), page_size // ad_interval)
        organic_count = page_size - ads_per_page

        organic = await get_organic(
            uow=self.uow,
            preferences=preferences,
            filters=filters or FeedFilters(),
            cursor=cursor,
            count=organic_count,
        )

        cards, last = organic
        if last:
            last_created, last_id = last
        else:
            return FeedPage(items=[],next_cursor=None)

        new_position = cursor.position if cursor else 0
        next_cursor = encode_cursor(
            FeedCursor(
                created_at=last_created,
                id=last_id,
                position=new_position + len(cards)
            )
        )

        await self.cache.set_json(
            key=cache_key,
            value={"items": [c.model_dump(mode="json") for c in cards], "next_cursor": next_cursor},
            ttl=settings.FEED_PAGE_CACHE_TTL_SECONDS,
        )

        if not ads:
            return FeedPage(items=cards, next_cursor=next_cursor)

        ad_start = (new_position // ad_interval) % len(ads)

        cards_ads = self._inject_ads(
            organic=cards, ads=ads, ad_interval=ad_interval, ad_start=ad_start
        )

        return FeedPage(items=cards_ads,next_cursor=next_cursor)

    @staticmethod
    def _inject_ads(
        *,
        organic: list[PropertyCardSchema],
        ads: list[PropertyCardSchema],
        ad_interval: int,
        ad_start: int,
    ) -> list[PropertyCardSchema]:
        feed: list[PropertyCardSchema] = []
        ad_index = ad_start
        for i, prop in enumerate(organic, start=1):
            feed.append(prop)
            if i % ad_interval == 0 and ads:
                feed.append(ads[ad_index % len(ads)])
                ad_index += 1
        return feed
