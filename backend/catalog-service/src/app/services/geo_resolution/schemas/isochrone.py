import uuid
from typing import Literal

from pydantic import Field

from app.schemas.base import StrictBase

OrsProfile = Literal["foot-walking", "driving-car", "cycling-regular"]


class IsochroneRequest(StrictBase):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    range_seconds: list[int] = Field(min_length=1)
    profile: list[OrsProfile] = ["foot-walking"]
    property_id: uuid.UUID | None = None


class IsochroneProfileResult(StrictBase):
    profile: OrsProfile
    features: list[dict] | None = None
    error: str | None = None


class GeoJsonPolygon(StrictBase):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[list[float]]]


class IsochroneEntry(StrictBase):
    profile: OrsProfile
    range: float | None = None
    isochrone: GeoJsonPolygon | None = None


class ReachablePoiItem(StrictBase):
    name: str
    category: str | None = None
    latitude: float
    longitude: float
    full_address: str | None = None
    phone: str | None = None
    website: str | None = None


class ReachablePoisResult(StrictBase):
    profile: OrsProfile
    range: float | None = None
    isochrone: GeoJsonPolygon | None = None
    pois: list[ReachablePoiItem] = []
    error: str | None = None
