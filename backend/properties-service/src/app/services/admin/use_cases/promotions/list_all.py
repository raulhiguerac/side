from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.helpers.cache_keys import feed_ads_global
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema


class ListAllPromotionsUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self) -> list[PropertyCardSchema]:
        try:
            cached = await self.cache.get_json(key=feed_ads_global())
            if cached:
                return [PropertyCardSchema.model_validate(c) for c in cached]
        except Exception:
            pass

        promotions = await run_in_threadpool(self.uow.promotions.get_all)
        if not promotions:
            return []

        property_ids = [p.property_id for p in promotions]
        properties = await run_in_threadpool(
            partial(self.uow.properties.get_by_ids, property_ids=property_ids)
        )

        cards = [PropertyCardSchema.model_validate(p) for p in properties]

        try:
            await self.cache.set_json(
                key=feed_ads_global(),
                value=[c.model_dump(mode="json") for c in cards],
            )
        except Exception:
            pass

        return cards
