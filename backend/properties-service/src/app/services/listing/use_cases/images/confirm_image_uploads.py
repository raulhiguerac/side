import uuid
from datetime import UTC, datetime
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.listing import (
    BatchExpiredError,
    BatchInvalidStateError,
    BatchNotConsistentError,
    BatchNotFoundError,
)
from app.core.exceptions.storage import StorageMisconfiguredError
from app.models.property import BatchStatus, PropertyImage
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.property_guard import get_owned_property_for_update
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property, client_properties, property_image_ids
from app.services.shared.ports.cache import CachePort


class ConfirmImageUploadsUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache = cache_client

        if not settings.BUCKET_PHOTOS_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_PHOTOS_PROPERTIES"})
        if not settings.STORAGE_PUBLIC_BASE_URL:
            raise StorageMisconfiguredError(context={"missing": "STORAGE_PUBLIC_BASE_URL"})

        self.base_url = settings.STORAGE_PUBLIC_BASE_URL.rstrip("/")
        self.bucket = settings.BUCKET_PHOTOS_PROPERTIES

    async def execute(
        self,
        *,
        principal: Principal,
        property_id: uuid.UUID,
        batch_id: uuid.UUID,
        confirmed_keys: list[str],
    ) -> None:
        await get_owned_property_for_update(uow=self.uow, property_id=property_id, principal=principal)

        batch = await run_in_threadpool(
            partial(self.uow.property_images.get_batch, batch_id=batch_id)
        )

        if batch is None:
            raise BatchNotFoundError(batch_id=batch_id)

        if batch.property_id != property_id:
            raise BatchNotConsistentError(batch_id=batch_id, expected=0, got=0)

        if datetime.now(UTC) > batch.expires_at:
            batch.status = BatchStatus.expired
            try:
                await self.uow.commit()
            except Exception:
                await self.uow.rollback()
            raise BatchExpiredError(batch_id=batch_id)

        if batch.status != BatchStatus.ready:
            if batch.status == BatchStatus.pending:
                batch.status = BatchStatus.failed
                try:
                    await self.uow.commit()
                except Exception:
                    await self.uow.rollback()
            raise BatchInvalidStateError(batch_id=batch_id, status=batch.status.value)

        expected_set = set(batch.expected_keys)
        confirmed_set = set(confirmed_keys)
        if not confirmed_set.issubset(expected_set):
            raise BatchNotConsistentError(
                batch_id=batch_id,
                expected=len(expected_set),
                got=len(confirmed_set),
            )

        new_images = [
            PropertyImage(
                property_id=batch.property_id,
                url=f"{self.base_url}/{self.bucket}/{key}",
                created_by=principal.sub,
                updated_by=principal.sub,
            )
            for key in confirmed_keys
        ]

        batch.status = BatchStatus.confirmed
        batch.confirmed_at = datetime.now(UTC)

        try:
            for image in new_images:
                await run_in_threadpool(partial(self.uow.property_images.add, image=image))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache.delete(key=[
                cache_property(property_id=batch.property_id),
                client_properties(user_id=principal.sub),
                property_image_ids(batch.property_id),
            ])
        except Exception:
            pass
