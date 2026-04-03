import uuid
from functools import partial
from datetime import datetime, UTC

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import (
    DeletePropertyError,
    PropertyForbiddenError,
    PropertyNotFoundError,
)
from app.models.property import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property, client_properties
from app.services.shared.ports.cache import CachePort

class DeletePropertyUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, property_id: uuid.UUID, principal: Principal) -> None:
        try:
            prop = await run_in_threadpool(
                partial(self.uow.properties.get_property, property_id=property_id)
            )
        except Exception as exc:
            raise translate_db_error(exc) from exc

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        if prop.owner_id != principal.sub:
            raise PropertyForbiddenError(property_id=property_id)

        prop.status = ListingStatus.inactive
        prop.deleted_at = datetime.now(UTC)
        prop.deleted_by = principal.sub

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise DeletePropertyError(cause=exc, context={"property_id": str(property_id)}) from exc

        try:
            await self.cache.delete(cache_property(property_id=property_id))
            await self.cache.delete(client_properties(user_id=principal.sub))
        except Exception:
            pass
