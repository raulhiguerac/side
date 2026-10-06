import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import CreatePropertyError, PropertyForbiddenError, PropertyNotFoundError
from app.models.image import ImageStatus
from app.models.listing import VerificationStatus
from app.schemas.principal import Principal
from app.services.listing.use_cases.images.delete_property_images import DeletePropertyImagesUseCase

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
IMAGE_ID_1 = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
IMAGE_ID_2 = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
PRINCIPAL = Principal(sub=OWNER_ID)


def _make_mock_image(image_id: uuid.UUID):
    m = MagicMock()
    m.id = image_id
    m.status = ImageStatus.active
    return m


def _make_prop(verification_status=VerificationStatus.verified):
    m = MagicMock()
    m.id = PROP_ID
    m.owner_id = OWNER_ID
    m.verification_status = verification_status
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
def uc(mock_uow, mock_cache):
    return DeletePropertyImagesUseCase(uow=mock_uow, cache_client=mock_cache)


# ---------------------------------------------------------------------------
# Early returns
# ---------------------------------------------------------------------------

async def test_returns_immediately_when_image_ids_empty(uc, mock_uow):
    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[])

    mock_uow.commit.assert_not_awaited()


@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_returns_without_commit_when_no_images_found(mock_get_prop, mock_run, uc, mock_uow):
    mock_run.return_value = []  # no images found

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    mock_uow.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_marks_images_pending_delete_and_invalidates_cache(mock_get_prop, mock_run, uc, mock_uow, mock_cache):
    images = [_make_mock_image(IMAGE_ID_1), _make_mock_image(IMAGE_ID_2)]
    mock_run.return_value = images

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1, IMAGE_ID_2])

    for image in images:
        assert image.status == ImageStatus.pending_delete

    mock_uow.commit.assert_awaited_once()
    mock_cache.delete.assert_awaited_once()


# ---------------------------------------------------------------------------
# Verification degradation — borrar fotos también invalida el sello
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_degrades_verification_when_property_was_verified(mock_get_prop, mock_run, uc, mock_uow):
    prop = _make_prop(verification_status=VerificationStatus.verified)
    mock_get_prop.return_value = prop
    mock_run.return_value = [_make_mock_image(IMAGE_ID_1)]

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    assert prop.verification_status == VerificationStatus.pending
    mock_uow.commit.assert_awaited_once()


@pytest.mark.parametrize(
    "initial",
    [VerificationStatus.unverified, VerificationStatus.pending, VerificationStatus.rejected],
)
@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_leaves_verification_untouched_when_not_verified(mock_get_prop, mock_run, uc, initial):
    prop = _make_prop(verification_status=initial)
    mock_get_prop.return_value = prop
    mock_run.return_value = [_make_mock_image(IMAGE_ID_1)]

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    assert prop.verification_status == initial


@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_does_not_degrade_when_no_images_matched(mock_get_prop, mock_run, uc):
    """El early return corta antes de degradar: pedir el borrado de ids que no
    existen no debe costarle la verificación al dueño."""
    prop = _make_prop(verification_status=VerificationStatus.verified)
    mock_get_prop.return_value = prop
    mock_run.return_value = []

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    assert prop.verification_status == VerificationStatus.verified


# ---------------------------------------------------------------------------
# Not found / forbidden
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_not_found(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyNotFoundError(property_id=PROP_ID)

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    mock_uow.commit.assert_not_awaited()


@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_raises_forbidden(mock_get_prop, uc, mock_uow):
    mock_get_prop.side_effect = PropertyForbiddenError(property_id=PROP_ID)

    with pytest.raises(PropertyForbiddenError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.delete_property_images.translate_db_error")
@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_rolls_back_and_raises_on_commit_error(mock_get_prop, mock_run, mock_translate, uc, mock_uow):
    mock_run.return_value = [_make_mock_image(IMAGE_ID_1)]
    mock_uow.commit.side_effect = Exception("db error")
    mock_translate.return_value = CreatePropertyError(cause=Exception("db error"))

    with pytest.raises(CreatePropertyError):
        await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    mock_uow.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache failure is swallowed
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.images.delete_property_images.run_in_threadpool")
@patch("app.services.listing.use_cases.images.delete_property_images.get_owned_property_for_update", new_callable=AsyncMock)
async def test_survives_cache_delete_failure(mock_get_prop, mock_run, uc, mock_uow, mock_cache):
    mock_run.return_value = [_make_mock_image(IMAGE_ID_1)]
    mock_cache.delete.side_effect = Exception("Redis down")

    await uc.execute(principal=PRINCIPAL, property_id=PROP_ID, image_ids=[IMAGE_ID_1])

    mock_uow.commit.assert_awaited_once()
