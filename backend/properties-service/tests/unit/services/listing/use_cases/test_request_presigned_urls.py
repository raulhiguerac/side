import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import ImageCountExceededError
from app.core.exceptions.storage import StorageMisconfiguredError
from app.schemas.principal import Principal
from app.services.listing.schemas.listing_schemas import PresignedUrlsRequest
from app.services.listing.use_cases.images.request_presigned_urls import RequestPresignedUrlsUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
PRINCIPAL = Principal(sub=OWNER_ID)

REQUEST = PresignedUrlsRequest(property_id=PROP_ID, create_count=2)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.property_images = MagicMock()
    return uow


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.generate_presigned_put_urls.return_value = ["https://upload.test/key1", "https://upload.test/key2"]
    return storage


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(monkeypatch, mock_uow, mock_storage, mock_cache):
    from app.core.config.settings import settings
    monkeypatch.setattr(settings, "BUCKET_PHOTOS_PROPERTIES", "test-bucket")
    monkeypatch.setattr(settings, "STORAGE_PUBLIC_BASE_URL", "https://storage.test")
    return RequestPresignedUrlsUseCase(uow=mock_uow, storage=mock_storage, cache=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.request_presigned_urls.check_image_count", new_callable=AsyncMock)
@patch("app.services.listing.use_cases.images.request_presigned_urls.get_owned_property_for_update", new_callable=AsyncMock)
@patch("app.services.listing.use_cases.images.request_presigned_urls.run_in_threadpool")
async def test_creates_batch_and_returns_presigned_urls(
    mock_run, mock_get_prop, mock_check_count, uc, mock_uow, mock_storage
):
    mock_run.return_value = None
    mock_check_count.return_value = 2

    result = await uc.execute(principal=PRINCIPAL, request=REQUEST)

    assert result.batch_id is not None
    assert len(result.items) == 2
    assert all(item.public_url.startswith("https://storage.test") for item in result.items)
    # batch was persisted and status set to ready
    assert mock_uow.commit.await_count == 2  # once for add_batch, once for status=ready


# ---------------------------------------------------------------------------
# Image count exceeded
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.request_presigned_urls.check_image_count", new_callable=AsyncMock)
@patch("app.services.listing.use_cases.images.request_presigned_urls.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_image_count_exceeded(mock_get_prop, mock_check_count, uc, mock_uow):
    mock_check_count.side_effect = ImageCountExceededError(max=20, requested=25)

    with pytest.raises(ImageCountExceededError):
        await uc.execute(principal=PRINCIPAL, request=REQUEST)

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Storage error — batch marked failed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.request_presigned_urls.check_image_count", new_callable=AsyncMock)
@patch("app.services.listing.use_cases.images.request_presigned_urls.get_owned_property_for_update", new_callable=AsyncMock)
@patch("app.services.listing.use_cases.images.request_presigned_urls.run_in_threadpool")
async def test_marks_batch_failed_on_storage_error(
    mock_run, mock_get_prop, mock_check_count, uc, mock_uow, mock_storage
):
    mock_run.return_value = None
    mock_check_count.return_value = 2
    mock_storage.generate_presigned_put_urls.side_effect = Exception("Storage unavailable")

    with pytest.raises(Exception, match="Storage unavailable"):
        await uc.execute(principal=PRINCIPAL, request=REQUEST)

    # First commit (add_batch) + second commit (mark failed) = 2 commits
    assert mock_uow.commit.await_count == 2


# ---------------------------------------------------------------------------
# Misconfigured settings raises at init time
# ---------------------------------------------------------------------------

def test_raises_storage_misconfigured_when_bucket_missing():
    with pytest.raises(StorageMisconfiguredError):
        RequestPresignedUrlsUseCase(
            uow=MagicMock(),
            storage=AsyncMock(),
            cache=AsyncMock(),
        )
