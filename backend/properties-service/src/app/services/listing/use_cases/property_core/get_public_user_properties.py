import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import public_user_properties
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema, PublicUserPropertiesResponse


class GetPublicUserPropertiesUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, user_id: uuid.UUID, offset: int) -> PublicUserPropertiesResponse:
        try:
            cache_key = public_user_properties(user_id=user_id, offset=offset)
            cached = await self.cache.get_json(key=cache_key)
            if cached is not None:
                return PublicUserPropertiesResponse.model_validate(cached)

            properties = await run_in_threadpool(
                partial(
                    self.uow.properties.get_public_user_properties,
                    user_id=user_id,
                    offset=offset
                )
            )

            has_more = len(properties) == settings.PUBLIC_PROPERTIES_PAGE_SIZE
            items = [PropertyCardSchema.model_validate(prop) for prop in properties[:20]]

            response = PublicUserPropertiesResponse(items=items, has_more=has_more)

            await self.cache.set_json(
                key=cache_key,
                value=response.model_dump(mode="json"),
                ttl=settings.CACHE_TTL_USER_PROPERTIES_SECONDS
            )

            return response
        except Exception as exc:
            raise translate_db_error(exc) from exc

