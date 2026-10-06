import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.listing import InvalidStatusTransitionError, PropertyNotFoundError, SetVisibilityError
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    feed_ads_by_city,
    feed_ads_global,
    map_h3_cell,
    public_user_properties_pattern,
)
from app.services.shared.helpers.status_transitions import LISTING_STATUS_TRANSITIONS
from app.services.shared.ports.cache import CachePort


class SetPropertyStatusUseCase:
    def __init__(self, *, uow: AdminUnitOfWork, cache: CachePort) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        target_status: ListingStatus,
    ) -> None:
        prop = await run_in_threadpool(
            partial(self.uow.properties.get_by_id, property_id=property_id)
        )

        if prop is None:
            raise PropertyNotFoundError(property_id=property_id)

        allowed = LISTING_STATUS_TRANSITIONS.get(prop.status, [])
        if target_status not in allowed:
            raise InvalidStatusTransitionError(
                current=prop.status.value,
                target=target_status.value,
            )

        prop.status = target_status
        prop.updated_by = principal.sub

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise SetVisibilityError(cause=exc, context={"property_id": str(property_id)}) from exc

        # Los ads del feed van con el resto: sacar de `active` una property
        # promocionada la deja sirviéndose como aviso pago hasta que expire el
        # TTL de esa entrada. Se invalidan pase lo que pase con el status —
        # saber si estaba promocionada costaría una query más, y borrar una key
        # que igual se repuebla al primer feed es más barato que consultarla.
        try:
            await self.cache.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=prop.owner_id),
                feed_ads_global(),
                *([feed_ads_by_city(prop.location.city_id)] if prop.location else []),
                *[map_h3_cell(i) for i in [prop.h3_r9, prop.h3_r7]],
            ])
            await self.cache.delete_pattern(
                pattern=public_user_properties_pattern(user_id=prop.owner_id)
            )
        except Exception:
            pass
