import uuid
from datetime import datetime, timezone

from app.core.exceptions.listing import DeletePropertyError
from app.models.listing import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    feed_ads_by_city,
    feed_ads_global,
    public_user_properties_pattern,
)
from app.services.shared.ports.cache import CachePort


class DeletePropertyUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, *, property_id: uuid.UUID, principal: Principal) -> None:
        prop = await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        prop.status = ListingStatus.inactive
        prop.deleted_at = datetime.now(timezone.utc)
        prop.deleted_by = principal.sub

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise DeletePropertyError(cause=exc, context={"property_id": str(property_id)}) from exc

        # Los ads del feed también: una property promocionada que se borra seguiría
        # sirviéndose como aviso pago hasta que expire el TTL de esa entrada.
        try:
            await self.cache.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=principal.sub),
                feed_ads_global(),
                *([feed_ads_by_city(prop.location.city_id)] if prop.location else []),
            ])
        except Exception:
            pass

        try:
            await self.cache.delete_pattern(
                pattern=public_user_properties_pattern(user_id=principal.sub)
            )
        except Exception:
            pass
