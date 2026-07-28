import uuid

from app.core.config.settings import settings
from app.core.exceptions.storage import StorageMisconfiguredError
from app.core.files.policies import PROPERTIES_BULK_UPLOAD_POLICY
from app.core.files.validators import validate_file_extension
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import BulkUploadUrlRequest, BulkUploadUrlResponse
from app.services.shared.ports.storage import StoragePort


class RequestBulkUploadUrlUseCase:
    """Hands the admin a presigned PUT so the CSV goes straight to storage
    instead of through the API. No job row is created here — that happens when
    the client comes back with the resulting key."""

    def __init__(self, *, storage: StoragePort) -> None:
        self.storage = storage

        if not settings.BUCKET_BULK_PROPERTIES:
            raise StorageMisconfiguredError(context={"missing": "BUCKET_BULK_PROPERTIES"})

        self.bucket = settings.BUCKET_BULK_PROPERTIES

    async def execute(
            self,
            *,
            principal: Principal,
            request: BulkUploadUrlRequest,
        ) -> BulkUploadUrlResponse:
        # The only check still possible once the upload bypasses the API — size
        # can't be enforced on a presigned PUT, so it's returned as a hint.
        ext = validate_file_extension(request.filename, PROPERTIES_BULK_UPLOAD_POLICY.allowed_extensions)

        key = f"{principal.sub}/{uuid.uuid4()}{ext}"

        upload_url = await self.storage.generate_presigned_put_url(
            bucket = self.bucket,
            key = key,
            ttl = settings.PRESIGNED_URL_TTL_SECONDS,
        )

        return BulkUploadUrlResponse(
            storage_key = key,
            upload_url = upload_url,
            max_size_bytes = PROPERTIES_BULK_UPLOAD_POLICY.max_size_bytes,
            expires_in = settings.PRESIGNED_URL_TTL_SECONDS,
        )
