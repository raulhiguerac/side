import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from typing import Optional

from app.core.config.settings import settings
from app.models.property import ListingStatus
from app.core.exceptions.listing import PropertyNotFoundError
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property
from app.services.shared.ports.cache import CachePort
from app.services.shared.schemas.property_detail import PropertyDetailSchema


class GetPropertyUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        property_id: uuid.UUID,
        principal: Optional[Principal] = None,
    ) -> PropertyDetailSchema:
        cache_key = cache_property(property_id=property_id)

        try:
            cached = await self.cache.get_json(key=cache_key)
            if cached:
                return PropertyDetailSchema.model_validate(cached)
        except Exception:
            pass

        try:
            prop = await run_in_threadpool(
                partial(self.uow.properties.get_by_id, property_id=property_id)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        is_owner = principal is not None and principal.sub == prop.owner_id
        if prop.status != ListingStatus.active and not is_owner:
            raise PropertyNotFoundError(property_id=property_id)

        result = PropertyDetailSchema.model_validate(prop)

        if prop.status == ListingStatus.active:
            try:
                await self.cache.set_json(
                    key=cache_key,
                    value=result.model_dump(mode="json"),
                    ttl=settings.CACHE_TTL_PROPERTY_SECONDS,
                )
            except Exception:
                pass

        return result
