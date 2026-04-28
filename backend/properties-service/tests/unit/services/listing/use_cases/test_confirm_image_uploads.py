import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import (
    BatchExpiredError,
    BatchInvalidStateError,
    BatchNotConsistentError,
    BatchNotFoundError,
)
from app.core.exceptions.storage import StorageMisconfiguredError
from app.models.property import BatchStatus
from app.schemas.principal import Principal
from app.services.listing.use_cases.images.confirm_image_uploads import ConfirmImageUploadsUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
BATCH_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OWNER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
PRINCIPAL = Principal(sub=OWNER_ID)

KEY_1 = f"{PROP_ID}/key-one"
KEY_2 = f"{PROP_ID}/key-two"


def _make_batch(status=BatchStatus.ready, expired=False, property_id=PROP_ID):
    m = MagicMock()
    m.id = BATCH_ID
    m.property_id = property_id
    m.status = status
    m.expected_keys = [KEY_1, KEY_2]
    m.expires_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(hours=1)
    )
    return m


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.property_images = MagicMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def uc(monkeypatch, mock_uow, mock_cache):
    from app.core.config.settings import settings
    monkeypatch.setattr(settings, "BUCKET_PHOTOS_PROPERTIES", "test-bucket")
    monkeypatch.setattr(settings, "STORAGE_PUBLIC_BASE_URL", "https://storage.test")
    return ConfirmImageUploadsUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_confirms_images_and_invalidates_cache(mock_get_prop, mock_run, uc, mock_uow, mock_cache):
    batch = _make_batch(status=BatchStatus.ready)
    mock_run.return_value = batch

    await uc.execute(
        principal=PRINCIPAL,
        property_id=PROP_ID,
        batch_id=BATCH_ID,
        confirmed_keys=[KEY_1],
    )

    assert batch.status == BatchStatus.confirmed
    assert batch.confirmed_at is not None
    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Batch not found
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_batch_not_found(mock_get_prop, mock_run, uc, mock_uow):
    mock_run.return_value = None

    with pytest.raises(BatchNotFoundError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[KEY_1],
        )


# ---------------------------------------------------------------------------
# Batch property mismatch
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_batch_not_consistent_when_property_mismatch(mock_get_prop, mock_run, uc):
    different_prop = uuid.uuid4()
    batch = _make_batch(property_id=different_prop)
    mock_run.return_value = batch

    with pytest.raises(BatchNotConsistentError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[KEY_1],
        )


# ---------------------------------------------------------------------------
# Batch expired
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_batch_expired_and_marks_expired(mock_get_prop, mock_run, uc, mock_uow):
    batch = _make_batch(status=BatchStatus.ready, expired=True)
    mock_run.return_value = batch

    with pytest.raises(BatchExpiredError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[KEY_1],
        )

    assert batch.status == BatchStatus.expired
    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Batch in pending state — marks failed and raises
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_marks_batch_failed_when_still_pending(mock_get_prop, mock_run, uc, mock_uow):
    batch = _make_batch(status=BatchStatus.pending)
    mock_run.return_value = batch

    with pytest.raises(BatchInvalidStateError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[KEY_1],
        )

    assert batch.status == BatchStatus.failed
    mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# Batch already confirmed — raises without changing status
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_invalid_state_for_already_confirmed_batch(mock_get_prop, mock_run, uc, mock_uow):
    batch = _make_batch(status=BatchStatus.confirmed)
    mock_run.return_value = batch

    with pytest.raises(BatchInvalidStateError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[KEY_1],
        )

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Keys not a subset of expected
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.confirm_image_uploads.run_in_threadpool")
@patch("app.services.listing.use_cases.images.confirm_image_uploads.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_batch_not_consistent_when_keys_not_subset(mock_get_prop, mock_run, uc):
    batch = _make_batch(status=BatchStatus.ready)
    mock_run.return_value = batch
    rogue_key = f"{PROP_ID}/not-in-batch"

    with pytest.raises(BatchNotConsistentError):
        await uc.execute(
            principal=PRINCIPAL,
            property_id=PROP_ID,
            batch_id=BATCH_ID,
            confirmed_keys=[rogue_key],
        )


# ---------------------------------------------------------------------------
# Misconfigured settings at init
# ---------------------------------------------------------------------------

def test_raises_storage_misconfigured_when_bucket_missing():
    with pytest.raises(StorageMisconfiguredError):
        ConfirmImageUploadsUseCase(uow=MagicMock(), cache_client=AsyncMock())
