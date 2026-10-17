import uuid
from typing import Annotated

from pydantic import Field, model_validator

from app.schemas.base import StrictBase
from app.schemas.pagination import Page, PageRequest

_MAX_BBOX_SIDE = 0.135  # ~15 km

Lon = Annotated[float, Field(ge=-180, le=180)]
Lat = Annotated[float, Field(ge=-90, le=90)]


class CreateNeighborhoodRequest(StrictBase):
    locality_id: uuid.UUID
    code: str
    name: str
    postal_code: str | None = None
    latitude: float
    longitude: float


class UpdateNeighborhoodRequest(StrictBase):
    name: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool | None = None


class NeighborhoodAdminResponse(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    code: str
    name: str
    postal_code: str | None
    latitude: float
    longitude: float
    is_active: bool


class NeighborhoodAdminDetail(NeighborhoodAdminResponse):
    geometry: dict | None = None
    area_m2: float | None = None


class ListNeighborhoodsAdminRequest(PageRequest):
    locality_id: uuid.UUID | None = None
    is_active: bool | None = None
    has_geometry: bool | None = None
    search_term: str | None = None


class NeighborhoodAdminListItem(StrictBase):
    id: uuid.UUID
    locality_id: uuid.UUID
    code: str
    name: str
    is_active: bool
    has_geometry: bool
    svg_path: str | None = None
    bbox: tuple[float, float, float, float] | None = None


class NeighborhoodCoverage(StrictBase):
    with_geometry: int
    total: int


class NeighborhoodAdminPage(Page[NeighborhoodAdminListItem]):
    coverage: NeighborhoodCoverage


class ListNeighborhoodGeometriesRequest(StrictBase):
    neighborhood_id: uuid.UUID
    bbox: tuple[Lon, Lat, Lon, Lat]

    @model_validator(mode="after")
    def _check_bbox(self) -> "ListNeighborhoodGeometriesRequest":
        min_lon, min_lat, max_lon, max_lat = self.bbox
        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError("bbox: min debe ser menor que max")
        if max_lon - min_lon > _MAX_BBOX_SIDE or max_lat - min_lat > _MAX_BBOX_SIDE:
            raise ValueError(f"bbox: cada lado debe medir como máximo {_MAX_BBOX_SIDE}°")
        return self


class NeighborhoodGeometryItem(StrictBase):
    id: uuid.UUID
    name: str
    geometry: dict


class BulkCreateNeighborhoodsResult(StrictBase):
    created: int
    errors: list[str]


class BulkEnrichNeighborhoodGeometriesResult(StrictBase):
    matched: int
    unmatched: list[str]
    updated: int
