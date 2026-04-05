import uuid

from app.core.config.settings import settings
from app.core.exceptions.listing import ImageCountExceededError
from app.core.exceptions.storage import StorageMisconfiguredError
from app.schemas.principal import Principal
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.schemas.listing_schemas import PresignedUrlItem
from app.services.shared.ports.storage import StoragePort


class RequestPresignedUrlsUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, storage: StoragePort) -> None:
        self.uow = uow
        self.storage = storage

        if not settings.BUCKET_PHOTOS_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_PHOTOS_PROPERTIES"})
        if not settings.STORAGE_PUBLIC_BASE_URL:
            raise StorageMisconfiguredError(context={"missing": "STORAGE_PUBLIC_BASE_URL"})

        self.bucket = settings.BUCKET_PHOTOS_PROPERTIES
        self.base_url = settings.STORAGE_PUBLIC_BASE_URL.rstrip("/")

    async def execute(
        self,
        principal: Principal,
        property_id: uuid.UUID,
        count: int,
    ) -> list[PresignedUrlItem]:
        if count < 1:
            return []

        if count > settings.MAX_IMAGES_PER_PROPERTY:
            raise ImageCountExceededError(max=settings.MAX_IMAGES_PER_PROPERTY, requested=count)

        await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        keys = [f"{property_id}/{uuid.uuid4()}" for _ in range(count)]
        upload_urls = await self.storage.generate_presigned_put_urls(
            bucket=self.bucket,
            keys=keys,
            ttl=settings.PRESIGNED_URL_TTL_SECONDS,
        )

        return [
            PresignedUrlItem(
                upload_url=upload_url,
                public_url=f"{self.base_url}/{self.bucket}/{key}",
                key=key,
            )
            for key, upload_url in zip(keys, upload_urls)
        ]
