from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import client_properties
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_card import PropertyCardSchema


class GetMyPropertiesUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, principal: Principal) -> list[PropertyCardSchema]:
        cache_key = client_properties(user_id=principal.sub)

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return [PropertyCardSchema.model_validate(prop) for prop in cached]
        except Exception:
            pass

        try:
            properties = await run_in_threadpool(
                partial(self.uow.properties.get_user_properties, user_id=principal.sub)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        result = [PropertyCardSchema.model_validate(prop) for prop in properties]

        try:
            await self.cache.set_json(
                key=cache_key,
                value=[prop.model_dump(mode="json") for prop in result],
                ttl=settings.CACHE_TTL_USER_PROPERTIES_SECONDS,
            )
        except Exception:
            pass

        return result
