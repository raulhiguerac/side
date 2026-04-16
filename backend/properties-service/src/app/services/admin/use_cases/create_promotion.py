from datetime import datetime, timedelta, timezone
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import PromotionError, PropertyNotFoundError
from app.models.property import PromotedListing
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.admin.schemas.admin_schemas import CreatePromotionRequest
from app.services.shared.helpers.cache_keys import client_properties, feed_ads_by_city, feed_ads_global
from app.services.shared.ports.cache import CachePort


class CreatePromotionUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, principal: Principal, promotion_request: CreatePromotionRequest) -> None:
        property_id = promotion_request.property_id
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        now = datetime.now(timezone.utc)
        promotion = PromotedListing(
            property_id=property_id,
            is_active=True,
            starts_at=now,
            ends_at=now + timedelta(days=promotion_request.promoted_days),
            priority=promotion_request.priority,
            created_by=principal.sub,
            updated_by=principal.sub,
        )

        try:
            await run_in_threadpool(partial(self.uow.promotions.add, promotion=promotion))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise PromotionError(cause=exc, context={"property_id": str(property_id)}) from exc

        try:
            await self.cache.delete(key=[
                feed_ads_global(),
                client_properties(user_id=prop.owner_id),
                *([feed_ads_by_city(prop.location.city_id)] if prop.location else []),
            ])
        except Exception:
            pass