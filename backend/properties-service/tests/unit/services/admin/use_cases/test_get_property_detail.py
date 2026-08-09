import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import PropertyNotFoundError
from app.models.listing import ListingStatus, VerificationStatus
from app.services.admin.schemas.admin_schemas import AdminPropertyDetailSchema
from app.services.admin.use_cases.get_property_detail import GetPropertyDetailAdminUseCase
from app.services.shared.helpers.cache_keys import cache_property

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

MODULE = "app.services.admin.use_cases.get_property_detail"


def _detail_payload(
    *,
    status: ListingStatus = ListingStatus.active,
    verification_status: VerificationStatus = VerificationStatus.pending,
) -> dict:
    return {
        "id": str(PROP_ID),
        "property_type": "house",
        "listing_type": "sale",
        "condition": "used",
        "status": status.value,
        "verification_status": verification_status.value,
        "price": "100",
        "currency": "COP",
        "area_m2": "50",
        "bedrooms": 2,
        "bathrooms": "1",
        "parking_spots": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "images": [],
    }


def _make_mock_prop(
    *,
    status: ListingStatus = ListingStatus.active,
    verification_status: VerificationStatus = VerificationStatus.pending,
):
    """`SimpleNamespace` y no `MagicMock`: el schema valida `from_attributes`, así
    que un mock resolvería cualquier atributo opcional a un `MagicMock` y
    reventaría la validación de los campos que no se setean."""
    return SimpleNamespace(
        id = PROP_ID,
        property_type = "house",
        listing_type = "sale",
        condition = "used",
        status = status,
        verification_status = verification_status,
        price = Decimal("100"),
        currency = "COP",
        admin_fee = None,
        area_m2 = Decimal("50"),
        bedrooms = 2,
        bathrooms = Decimal("1"),
        parking_spots = 0,
        floor_number = None,
        total_floors = None,
        stratum = None,
        description = None,
        year_built = None,
        created_at = datetime.now(timezone.utc),
        location = None,
        images = [],
    )


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get_json.return_value = None
    return cache


@pytest.fixture
def uc(mock_uow, mock_cache):
    return GetPropertyDetailAdminUseCase(cache=mock_cache, uow=mock_uow)


# ---------------------------------------------------------------------------
# Los destinos legales viajan con el detalle
# ---------------------------------------------------------------------------

@patch(f"{MODULE}.run_in_threadpool")
async def test_returns_allowed_targets_for_current_state(mock_run, uc):
    mock_run.return_value = _make_mock_prop(
        status=ListingStatus.active,
        verification_status=VerificationStatus.pending,
    )

    result = await uc.execute(property_id=PROP_ID)

    assert isinstance(result, AdminPropertyDetailSchema)
    assert result.allowed_verification_targets == [
        VerificationStatus.verified,
        VerificationStatus.rejected,
    ]
    assert result.allowed_status_targets == [
        ListingStatus.draft,
        ListingStatus.inactive,
        ListingStatus.sold,
        ListingStatus.rented,
    ]


@patch(f"{MODULE}.run_in_threadpool")
async def test_unverified_cannot_reach_verified_in_one_step(mock_run, uc):
    mock_run.return_value = _make_mock_prop(
        verification_status=VerificationStatus.unverified
    )

    result = await uc.execute(property_id=PROP_ID)

    assert result.allowed_verification_targets == [VerificationStatus.pending]
    assert VerificationStatus.verified not in result.allowed_verification_targets


@patch(f"{MODULE}.run_in_threadpool")
async def test_terminal_status_offers_only_its_legal_target(mock_run, uc):
    mock_run.return_value = _make_mock_prop(status=ListingStatus.sold)

    result = await uc.execute(property_id=PROP_ID)

    assert result.allowed_status_targets == [ListingStatus.inactive]


async def test_cached_detail_also_gets_targets(uc, mock_cache):
    """El camino de cache guarda el schema público, así que los destinos se
    calculan igual al salir — si no, un hit devolvería el detalle sin ellos."""
    mock_cache.get_json.return_value = _detail_payload(
        verification_status=VerificationStatus.verified
    )

    result = await uc.execute(property_id=PROP_ID)

    assert isinstance(result, AdminPropertyDetailSchema)
    assert result.allowed_verification_targets == [
        VerificationStatus.pending,
        VerificationStatus.rejected,
    ]


# ---------------------------------------------------------------------------
# Lo que se escribe al cache no lleva los derivados
# ---------------------------------------------------------------------------

@patch(f"{MODULE}.run_in_threadpool")
async def test_cache_write_omits_derived_targets(mock_run, uc, mock_cache):
    """La entrada es la misma que sirve al detalle público: meterle campos
    admin-only la publicaría."""
    mock_run.return_value = _make_mock_prop(status=ListingStatus.active)

    await uc.execute(property_id=PROP_ID)

    cached_value = mock_cache.set_json.call_args.kwargs["value"]
    assert "allowed_verification_targets" not in cached_value
    assert "allowed_status_targets" not in cached_value
    assert mock_cache.set_json.call_args.kwargs["key"] == cache_property(property_id=PROP_ID)


@patch(f"{MODULE}.run_in_threadpool")
async def test_does_not_cache_non_active_properties(mock_run, uc, mock_cache):
    mock_run.return_value = _make_mock_prop(status=ListingStatus.draft)

    result = await uc.execute(property_id=PROP_ID)

    mock_cache.set_json.assert_not_awaited()
    assert result.allowed_status_targets == [ListingStatus.active]


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------

@patch(f"{MODULE}.run_in_threadpool")
async def test_raises_not_found_when_property_missing(mock_run, uc):
    mock_run.return_value = None

    with pytest.raises(PropertyNotFoundError):
        await uc.execute(property_id=PROP_ID)
