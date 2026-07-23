import uuid
from datetime import datetime, timedelta, timezone
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.config.settings import settings
from app.core.exceptions.storage import StorageMisconfiguredError
from app.models.image import BatchStatus, PropertyImageUploadBatch
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.image_count_guard import check_image_count
from app.services.listing.helpers.property_guard import get_owned_property_for_update
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.schemas.listing_schemas import PresignedUrlItem, PresignedUrlsRequest, PresignedUrlsResponse
from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.storage import StoragePort


class RequestPresignedUrlsUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, storage: StoragePort, cache: CachePort) -> None:
        self.uow = uow
        self.storage = storage
        self.cache = cache

        if not settings.BUCKET_PHOTOS_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_PHOTOS_PROPERTIES"})
        if not settings.STORAGE_PUBLIC_BASE_URL:
            raise StorageMisconfiguredError(context={"missing": "STORAGE_PUBLIC_BASE_URL"})

        self.bucket = settings.BUCKET_PHOTOS_PROPERTIES
        self.base_url = settings.STORAGE_PUBLIC_BASE_URL.rstrip("/")

    async def execute(
        self,
        *,
        principal: Principal,
        request: PresignedUrlsRequest,
    ) -> PresignedUrlsResponse:
        await get_owned_property_for_update(uow=self.uow, property_id=request.property_id, principal=principal)

        count = await check_image_count(
            uow=self.uow,
            cache=self.cache,
            property_id=request.property_id,
            create_count=request.create_count,
        )

        keys = [f"{request.property_id}/{uuid.uuid4()}" for _ in range(count)]

        batch = PropertyImageUploadBatch(
            property_id=request.property_id,
            owner_id=principal.sub,
            status=BatchStatus.pending,
            expected_keys=keys,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.IMAGE_UPLOAD_BATCH_TTL_SECONDS),
            created_by=principal.sub,
            updated_by=principal.sub,
        )

        try:
            await run_in_threadpool(partial(self.uow.property_images.add_batch, batch=batch))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            upload_urls = await self.storage.generate_presigned_put_urls(
                bucket=self.bucket,
                keys=keys,
                ttl=settings.PRESIGNED_URL_TTL_SECONDS,
            )
        except Exception as exc:
            batch.status = BatchStatus.failed
            try:
                await self.uow.commit()
            except Exception:
                pass
            raise exc

        batch.status = BatchStatus.ready
        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        return PresignedUrlsResponse(
            batch_id=batch.id,
            items=[
                PresignedUrlItem(
                    upload_url=upload_url,
                    public_url=f"{self.base_url}/{self.bucket}/{key}",
                    key=key,
                )
                for key, upload_url in zip(keys, upload_urls)
            ],
        )
