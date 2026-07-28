import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.image import ImageStatus
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.property_guard import get_owned_property_for_update
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import (
    cache_property,
    client_properties,
    property_image_ids,
    public_user_properties_pattern,
)
from app.services.shared.ports.cache import CachePort


class DeletePropertyImagesUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        image_ids: list[uuid.UUID],
    ) -> None:
        if not image_ids:
            return

        await get_owned_property_for_update(uow=self.uow, property_id=property_id, principal=principal)

        images = await run_in_threadpool(
            partial(
                self.uow.property_images.get_images,
                property_id=property_id,
                image_ids=image_ids,
            )
        )

        if not images:
            return

        for image in images:
            image.status = ImageStatus.pending_delete

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.delete(key=[
                cache_property(property_id=property_id),
                client_properties(user_id=principal.sub),
                property_image_ids(property_id),
            ])
            await self.cache_client.delete_pattern(
                pattern=public_user_properties_pattern(user_id=principal.sub)
            )
        except Exception:
            pass
