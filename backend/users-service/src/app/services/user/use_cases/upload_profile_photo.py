from typing import IO

from app.schemas.auth import Principal
from app.schemas.user import PhotoUploadOut

from app.services.user.ports.cache import CachePort
from app.services.user.ports.storage import StoragePort
from app.services.user.ports.unit_of_work import UserUnitOfWork

from app.services.shared.helpers.url_builder import build_public_url
from app.services.user.helpers.cache_keys import profile_cache_key
from app.services.user.helpers.storage_keys import profile_photo_storage_key

from app.services.user.helpers.current_account_reader import CurrentAccountReader
from app.services.user.helpers.current_profile_reader import CurrentProfileReader

class UpdateCurrentProfilePhotoUseCase:
    def __init__(
            self, 
            *,
            uow: UserUnitOfWork,
            cache_client: CachePort,
            storage_client: StoragePort,
            account_reader: CurrentAccountReader,
            profile_reader: CurrentProfileReader,
            bucket_name: str,
            base_url: str
        ):
        self.uow = uow
        self.cache_client = cache_client
        self.storage_client = storage_client
        self.account_reader = account_reader
        self.profile_reader = profile_reader
        self.bucket_name = bucket_name
        self.base_url = base_url

    async def execute(self, *, file: IO[bytes], content_type: str, principal: Principal) -> PhotoUploadOut:
        account_id = principal.sub
        key = profile_photo_storage_key(account_id=account_id)

        account = await self.account_reader.get_active(account_id=account_id)
        profile_db = await self.profile_reader.get_model(
            account_id=account_id, 
            account_type=account.account_type
        )

        key = profile_photo_storage_key(account_id=account_id)
        await self.storage_client.upload_file(
                fileobj=file,
                bucket=self.bucket_name,
                key=key,
                extra_args={"ContentType": content_type},
            )

        photo_url = build_public_url(base_url=self.base_url, bucket=self.bucket_name, key=key)
            
        profile_db.photo_url = photo_url
        profile_db.photo_key = key

        await self.uow.commit()

        cache_key = profile_cache_key(account_id=account_id)

        await self.cache_client.delete(key=cache_key)

        return PhotoUploadOut(photo_url=photo_url)