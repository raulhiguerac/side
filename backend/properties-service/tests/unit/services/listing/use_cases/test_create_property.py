import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.listing import CreatePropertyError, InconsistentLocationError
from app.models.listing import Currency, ListingType, PropertyCondition, PropertyType
from app.schemas.principal import Principal
from app.services.listing.schemas.listing_schemas import CreatePropertyRequest, LocationField
from app.services.listing.use_cases.property_core.create_property import CreatePropertyUseCase

OWNER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
NEIGHBORHOOD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
CITY_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
COUNTRY_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

PRINCIPAL = Principal(sub=OWNER_ID)

REQUEST = CreatePropertyRequest(
    property_type=PropertyType.apartment,
    listing_type=ListingType.sale,
    condition=PropertyCondition.used,
    currency=Currency.COP,
    floor_number=3,
    area_m2=Decimal("50.00"),
    bedrooms=2,
    bathrooms=Decimal("1.0"),
    price=Decimal("100000.00"),
    location=LocationField(
        neighborhood_id=NEIGHBORHOOD_ID,
        city_id=CITY_ID,
        country_id=COUNTRY_ID,
        latitude=4.6097,
        longitude=-74.0817,
    ),
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.properties = MagicMock()
    uow.property_locations = MagicMock()
    return uow


@pytest.fixture
def mock_catalog():
    catalog = AsyncMock()
    catalog.get_neighborhood.return_value = MagicMock(locality_id=CITY_ID)
    return catalog


@pytest.fixture
def uc(mock_uow, mock_catalog):
    return CreatePropertyUseCase(uow=mock_uow, catalog=mock_catalog)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.create_property.from_shape", return_value=MagicMock())
@patch("app.services.listing.use_cases.property_core.create_property.compute_h3", return_value=("r9cell", "r7cell"))
@patch("app.services.listing.use_cases.property_core.create_property.run_in_threadpool")
async def test_creates_property_and_commits(mock_run, _mock_h3, _mock_shape, uc, mock_uow, mock_catalog):
    mock_run.return_value = None

    await uc.execute(principal=PRINCIPAL, property_fields=REQUEST)

    mock_catalog.get_neighborhood.assert_awaited_once_with(neighborhood_id=NEIGHBORHOOD_ID)
    assert mock_run.await_count == 2  # properties.add + property_locations.add
    mock_uow.commit.assert_awaited_once()
    mock_uow.rollback.assert_not_awaited()


# ---------------------------------------------------------------------------
# Inconsistent location
# ---------------------------------------------------------------------------

async def test_raises_inconsistent_location_when_neighborhood_not_in_city(uc, mock_catalog):
    different_city = uuid.uuid4()
    mock_catalog.get_neighborhood.return_value = MagicMock(locality_id=different_city)

    with pytest.raises(InconsistentLocationError):
        await uc.execute(principal=PRINCIPAL, property_fields=REQUEST)

    mock_catalog.get_neighborhood.assert_awaited_once()


# ---------------------------------------------------------------------------
# DB error
# ---------------------------------------------------------------------------

@patch("app.services.listing.use_cases.property_core.create_property.translate_db_error")
@patch("app.services.listing.use_cases.property_core.create_property.from_shape", return_value=MagicMock())
@patch("app.services.listing.use_cases.property_core.create_property.compute_h3", return_value=("r9cell", "r7cell"))
@patch("app.services.listing.use_cases.property_core.create_property.run_in_threadpool")
async def test_rolls_back_and_raises_on_commit_error(mock_run, _mock_h3, _mock_shape, mock_translate, uc, mock_uow):
    mock_run.return_value = None
    mock_uow.commit.side_effect = Exception("db error")
    mock_translate.return_value = CreatePropertyError(cause=Exception("db error"))

    with pytest.raises(CreatePropertyError):
        await uc.execute(principal=PRINCIPAL, property_fields=REQUEST)

    mock_uow.rollback.assert_awaited_once()
