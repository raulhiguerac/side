import uuid

from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.schemas.listing_schemas import UpdatePropertyRequest
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    public_user_properties_pattern,
)
from app.services.shared.ports.cache import CachePort


class UpdatePropertyUseCase:
    def __init__(
        self,
        *,
        uow: ListingUnitOfWork,
        cache_client: CachePort,
    ) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        request: UpdatePropertyRequest,
    ) -> None:
        db_model = await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        data = request.model_dump(exclude_unset=True)

        for field, value in data.items():
            setattr(db_model, field, value)

        db_model.updated_by = principal.sub

        try:
            await self.uow.commit()
            await self.uow.refresh(db_model)
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.delete(key=[
                cache_property(property_id=db_model.id),
                client_properties(user_id=db_model.owner_id),
            ])
            await self.cache_client.delete_pattern(
                pattern=public_user_properties_pattern(user_id=db_model.owner_id)
            )
        except Exception:
            pass
