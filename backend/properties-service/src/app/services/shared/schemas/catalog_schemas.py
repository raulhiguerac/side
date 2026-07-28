import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class _ExternalSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class NeighborhoodInfo(_ExternalSchema):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str


class LocationInfo(_ExternalSchema):
    neighborhood_id: uuid.UUID
    city_id: uuid.UUID = Field(alias="locality_id")
    country_id: uuid.UUID


class PointToResolve(_ExternalSchema):
    id: str
    lat: float
    lon: float


class ResolvedPoint(_ExternalSchema):
    id: str
    location: Optional[LocationInfo] = None
