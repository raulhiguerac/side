import uuid

import pytest
from pydantic import ValidationError

from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodGeometriesRequest,
)

NEIGHBORHOOD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _request(bbox):
    return ListNeighborhoodGeometriesRequest(neighborhood_id=NEIGHBORHOOD_ID, bbox=bbox)


def test_accepts_valid_bbox():
    assert _request((-74.06, 4.67, -74.03, 4.69)).bbox == (-74.06, 4.67, -74.03, 4.69)


@pytest.mark.parametrize(
    "bbox",
    [
        (-74.03, 4.67, -74.06, 4.69),  # lon invertida
        (-74.06, 4.69, -74.03, 4.67),  # lat invertida
        (-74.06, 4.67, -74.06, 4.69),  # ancho cero
    ],
)
def test_rejects_min_not_below_max(bbox):
    with pytest.raises(ValidationError, match="min debe ser menor que max"):
        _request(bbox)


@pytest.mark.parametrize(
    "bbox",
    [
        (-74.20, 4.60, -74.00, 4.70),  # 0,2° de ancho
        (-74.10, 4.50, -74.00, 4.70),  # 0,2° de alto
    ],
)
def test_rejects_bbox_larger_than_limit(bbox):
    with pytest.raises(ValidationError, match="como máximo"):
        _request(bbox)


@pytest.mark.parametrize(
    "bbox",
    [
        (-181.0, 4.60, -74.00, 4.70),
        (-74.10, -91.0, -74.00, 4.70),
        (-74.10, 4.60, 181.0, 4.70),
        (-74.10, 4.60, -74.00, 91.0),
    ],
)
def test_rejects_coordinates_out_of_range(bbox):
    with pytest.raises(ValidationError):
        _request(bbox)


def test_rejects_bbox_with_three_values():
    with pytest.raises(ValidationError):
        _request((-74.06, 4.67, -74.03))
