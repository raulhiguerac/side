import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import InvalidStatusTransitionError, PropertyNotFoundError, SetVisibilityError
from app.models.property import ListingStatus
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    map_h3_cell,
    public_user_properties_pattern,
)
from app.services.shared.ports.cache import CachePort

_ALLOWED_TRANSITIONS: dict[ListingStatus, list[ListingStatus]] = {
    ListingStatus.draft: [ListingStatus.active],
    ListingStatus.active: [ListingStatus.draft, ListingStatus.inactive, ListingStatus.sold, ListingStatus.rented],
    ListingStatus.inactive: [ListingStatus.active, ListingStatus.draft],
    ListingStatus.sold: [ListingStatus.inactive],
    ListingStatus.rented: [ListingStatus.inactive],
}


class SetPropertyStatusUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, property_id: uuid.UUID, target_status: ListingStatus) -> None:
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        allowed = _ALLOWED_TRANSITIONS.get(prop.status, [])
        if target_status not in allowed:
            raise InvalidStatusTransitionError(
                current=prop.status.value,
                target=target_status.value,
            )

        prop.status = target_status

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise SetVisibilityError(cause=exc, context={"property_id": str(property_id)}) from exc

        try:
            await self.cache.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=prop.owner_id),
                *[map_h3_cell(i) for i in [prop.h3_r9, prop.h3_r7]],
            ])
            await self.cache.delete_pattern(
                pattern=public_user_properties_pattern(user_id=prop.owner_id)
            )
        except Exception:
            pass
