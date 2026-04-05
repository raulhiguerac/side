import uuid

from app.core.config.settings import settings
from app.core.exceptions.storage import StorageMisconfiguredError
from app.models.property import PropertyImage
from app.schemas.principal import Principal
from app.services.listing.helpers.db_error_translator import translate_db_error
from app.services.listing.helpers.property_guard import get_owned_property
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.shared.helpers.cache_keys import cache_property, client_properties
from app.services.shared.ports.cache import CachePort


class ConfirmImageUploadsUseCase:
    def __init__(self, *, uow: ListingUnitOfWork, cache_client: CachePort) -> None:
        self.uow = uow
        self.cache_client = cache_client

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
        property_id: uuid.UUID,
        keys: list[str],
    ) -> None:
        if not keys:
            return

        await get_owned_property(uow=self.uow, property_id=property_id, principal=principal)

        images = [
            PropertyImage(
                property_id=property_id,
                url=f"{self.base_url}/{self.bucket}/{key}",
                created_by=principal.sub,
                updated_by=principal.sub,
            )
            for key in keys
        ]

        try:
            for image in images:
                await self.uow.property_images.add(image=image)
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise translate_db_error(exc) from exc

        try:
            await self.cache_client.delete(key=cache_property(property_id=property_id))
            await self.cache_client.delete(key=client_properties(user_id=principal.sub))
        except Exception:
            pass
