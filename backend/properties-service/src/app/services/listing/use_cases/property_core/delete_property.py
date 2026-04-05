import uuid
from datetime import UTC, datetime

from app.core.exceptions.listing import DeletePropertyError
from app.models.property import ListingStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property, client_properties
from app.services.shared.ports.cache import CachePort


class DeletePropertyUseCase:
    def __init__(self, *, cache: CachePort, uow: ListingUnitOfWork) -> None:
        self.uow = uow
        self.cache = cache

    async def execute(self, property_id: uuid.UUID, principal: Principal) -> None:
        prop = await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

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
