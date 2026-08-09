import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.admin.schemas.admin_schemas import (
    AdminPromotionsPage,
    GetPromotionsAdminRequest,
)
from app.services.admin.use_cases.promotions.list_all import ListAllPromotionsUseCase

MODULE = "app.services.admin.use_cases.promotions.list_all"

PROP_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _promotion(priority: int = 3):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id = uuid.uuid4(),
        property_id = PROP_ID,
        priority = priority,
        starts_at = now,
        ends_at = now + timedelta(days=7),
        is_active = True,
        property = SimpleNamespace(
            id = PROP_ID,
            property_type = "house",
            listing_type = "sale",
            status = "active",
            price = Decimal("100"),
            currency = "COP",
            area_m2 = Decimal("50"),
            bedrooms = 2,
            bathrooms = Decimal("1"),
            parking_spots = 0,
            is_promoted = True,
            location = None,
            images = [],
        ),
    )


@pytest.fixture
def mock_uow():
    return MagicMock()


@pytest.fixture
def uc(mock_uow):
    return ListAllPromotionsUseCase(uow=mock_uow)


@patch(f"{MODULE}.run_in_threadpool")
async def test_returns_page_with_server_total(mock_run, uc):
    mock_run.side_effect = [[_promotion()], 42]

    result = await uc.execute(request=GetPromotionsAdminRequest(page=1, page_size=20))

    assert isinstance(result, AdminPromotionsPage)
    assert result.total == 42
    assert result.page == 1
    assert result.page_size == 20
    assert len(result.items) == 1


@patch(f"{MODULE}.run_in_threadpool")
async def test_promotion_carries_priority_dates_and_property(mock_run, uc):
    mock_run.side_effect = [[_promotion(priority=5)], 1]

    result = await uc.execute(request=GetPromotionsAdminRequest())

    item = result.items[0]
    assert item.priority == 5
    assert item.property_id == PROP_ID
    assert item.ends_at > item.starts_at
    # La property viaja anidada: sin eso la tabla no puede mostrar de qué se trata.
    assert item.property is not None
    assert item.property.id == PROP_ID


@patch(f"{MODULE}.run_in_threadpool")
async def test_translates_page_to_offset(mock_run, uc, mock_uow):
    mock_run.side_effect = [[], 0]

    await uc.execute(request=GetPromotionsAdminRequest(page=3, page_size=20))

    # El UC no toca la DB: arma el `partial` que corre en el threadpool.
    page_call = mock_run.call_args_list[0].args[0]
    assert page_call.keywords["offset"] == 40
    assert page_call.keywords["limit"] == 20


def test_use_case_takes_no_cache():
    """Cachear este listado significaba compartir `feed_ads_global()` con el feed
    público; se quitó al darle schema propio."""
    with pytest.raises(TypeError):
        ListAllPromotionsUseCase(uow=MagicMock(), cache=MagicMock())
