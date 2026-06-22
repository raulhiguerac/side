import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import public_user_properties
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema


class GetPublicUserPropertiesUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, user_id: uuid.UUID, offset: int) -> list[PropertyCardSchema]:
        try:
            cache_key = public_user_properties(user_id=user_id, offset=offset)
            cache_properties = await self.cache.get_json(key=cache_key)
            if cache_properties is not None:
                return [PropertyCardSchema.model_validate(prop) for prop in cache_properties]

            properties = await run_in_threadpool(
                partial(
                    self.uow.properties.get_public_user_properties,
                    user_id=user_id,
                    offset=offset
                )
            )

            result = [PropertyCardSchema.model_validate(prop) for prop in properties]

            await self.cache.set_json(
                key=cache_key,
                value=[prop.model_dump(mode="json") for prop in result],
                ttl=settings.CACHE_TTL_USER_PROPERTIES_SECONDS
            )

            return result
        except Exception as exc:
            raise translate_db_error(exc) from exc

