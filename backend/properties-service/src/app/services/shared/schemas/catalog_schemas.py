import uuid

from pydantic import BaseModel, ConfigDict


class _ExternalSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class NeighborhoodInfo(_ExternalSchema):
    id: uuid.UUID
    locality_id: uuid.UUID
    name: str


class LocationInfo(_ExternalSchema):
    neighborhood_id: uuid.UUID
    city_id: uuid.UUID
    country_id: uuid.UUID
