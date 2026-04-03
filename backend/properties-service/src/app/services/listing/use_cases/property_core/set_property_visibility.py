import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import (
    InvalidStatusTransitionError,
    PropertyForbiddenError,
    PropertyNotFoundError,
    SetVisibilityError,
)
from app.models.property import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property
from app.services.shared.ports.cache import CachePort

_ALLOWED_TRANSITIONS = {
    ListingStatus.draft: ListingStatus.active,
    ListingStatus.active: ListingStatus.draft,
}


class SetPropertyVisibilityUseCase:
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

        next_status = _ALLOWED_TRANSITIONS.get(prop.status)
        if next_status is None:
            raise InvalidStatusTransitionError(
                current=prop.status.value,
                target="draft/active",
            )

        prop.status = next_status

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise SetVisibilityError(cause=exc, context={"property_id": str(property_id)}) from exc

        try:
            await self.cache.delete(cache_property(property_id=property_id))
        except Exception:
            pass
