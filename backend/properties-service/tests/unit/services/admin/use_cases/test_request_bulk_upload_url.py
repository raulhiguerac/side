import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions.storage import StorageMisconfiguredError
from app.core.exceptions.validation import UnsupportedFileTypeError
from app.schemas.principal import Principal
from app.services.admin.schemas.admin_schemas import BulkUploadUrlRequest
from app.services.admin.use_cases.request_bulk_upload_url import RequestBulkUploadUrlUseCase

PRINCIPAL = Principal(sub=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def storage():
    s = AsyncMock()
    s.generate_presigned_put_url.return_value = "https://minio.test/signed"
    return s


@pytest.fixture
def uc(monkeypatch, storage):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BUCKET_BULK_PROPERTIES", "bulk-bucket")
    return RequestBulkUploadUrlUseCase(storage=storage)


async def test_returns_a_signed_url_for_the_bulk_bucket(uc, storage):
    result = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))

    assert result.upload_url == "https://minio.test/signed"
    assert storage.generate_presigned_put_url.await_args.kwargs["bucket"] == "bulk-bucket"


async def test_key_is_namespaced_per_admin_and_keeps_the_extension(uc):
    result = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))

    assert result.storage_key.startswith(f"{PRINCIPAL.sub}/")
    assert result.storage_key.endswith(".csv")


async def test_each_request_gets_a_distinct_key(uc):
    first = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))
    second = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))

    assert first.storage_key != second.storage_key


async def test_no_job_row_is_created_yet(uc, storage):
    """The BulkJob is born when the client comes back with the key, so an
    abandoned upload leaves nothing behind."""
    result = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))

    assert not hasattr(result, "batch_id")


@pytest.mark.parametrize("filename", ["payload.exe", "sheet.xlsx", "noext"])
async def test_rejects_disallowed_extensions(uc, storage, filename):
    with pytest.raises(UnsupportedFileTypeError):
        await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename=filename))

    storage.generate_presigned_put_url.assert_not_awaited()


async def test_extension_check_is_case_insensitive(uc):
    result = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="SEED.CSV"))

    assert result.storage_key.endswith(".csv")


async def test_size_limit_is_advisory_only(uc):
    """A plain presigned PUT can't cap the body, so the limit travels to the
    client as a hint rather than being enforced here."""
    result = await uc.execute(principal=PRINCIPAL, request=BulkUploadUrlRequest(filename="seed.csv"))

    assert result.max_size_bytes == 50 * 1024 * 1024
    assert result.expires_in > 0


def test_raises_when_the_bucket_is_not_configured(monkeypatch, storage):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BUCKET_BULK_PROPERTIES", "")
    with pytest.raises(StorageMisconfiguredError):
        RequestBulkUploadUrlUseCase(storage=storage)
