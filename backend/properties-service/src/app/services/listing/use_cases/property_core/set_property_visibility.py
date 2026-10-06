import uuid

from app.core.exceptions.listing import InvalidStatusTransitionError, SetVisibilityError
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    public_user_properties_pattern,
)
from app.services.shared.helpers.status_transitions import OWNER_VISIBILITY_TRANSITIONS
from app.services.shared.ports.cache import CachePort


class SetPropertyVisibilityUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, property_id: uuid.UUID, principal: Principal) -> None:
        prop = await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        next_status = OWNER_VISIBILITY_TRANSITIONS.get(prop.status)
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
            await self.cache.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=principal.sub)
            ])
            await self.cache.delete_pattern(
                pattern=public_user_properties_pattern(user_id=principal.sub)
            )
        except Exception:
            pass
