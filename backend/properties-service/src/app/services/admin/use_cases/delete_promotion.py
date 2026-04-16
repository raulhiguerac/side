import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import PromotionError, PromotionNotFoundError
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.helpers.cache_keys import client_properties, feed_ads_by_city, feed_ads_global
from app.services.shared.ports.cache import CachePort


class DeletePromotionUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, principal: Principal, property_id: uuid.UUID) -> None:
        promotion = await run_in_threadpool(
            partial(self.uow.promotions.get_active_by_property_id, property_id=property_id)
        )

        if promotion is None:
            raise PromotionNotFoundError(property_id=property_id)

        promotion.is_active = False

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise PromotionError(cause=exc, context={"property_id": str(property_id)}) from exc

        prop = promotion.property
        try:
            await self.cache.delete(key=[
                feed_ads_global(),
                client_properties(user_id=prop.owner_id),
                *([feed_ads_by_city(prop.location.city_id)] if prop.location else []),
            ])
        except Exception:
            pass