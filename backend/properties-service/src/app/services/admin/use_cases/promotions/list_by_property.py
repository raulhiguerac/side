import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import PromotionNotFoundError
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema


class ListPromotionsByPropertyUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, property_id: uuid.UUID) -> list[PropertyCardSchema]:
        try:
            cached = await self.cache.get_json(key=cache_property(property_id))
            if cached:
                card = PropertyCardSchema.model_validate(cached)
                if not card.is_promoted:
                    raise PromotionNotFoundError(property_id=property_id)
                return [card]
        except PromotionNotFoundError:
            raise
        except Exception:
            pass

        promotions = await run_in_threadpool(
            partial(self.uow.promotions.get_all_by_property_id, property_id=property_id)
        )

        if not promotions:
            raise PromotionNotFoundError(property_id=property_id)

        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )
        if prop is None:
            raise PromotionNotFoundError(property_id=property_id)

        card = PropertyCardSchema.model_validate(prop)

        try:
            await self.cache.set_json(
                key=cache_property(property_id),
                value=card.model_dump(mode="json"),
            )
        except Exception:
            pass

        return [card]
