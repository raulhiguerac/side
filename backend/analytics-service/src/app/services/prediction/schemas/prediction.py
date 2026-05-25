import uuid
from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import StrictBase
from app.models.prediction import PropertyType


class PredictionRequest(StrictBase):
    area_m2: float = Field(gt=0, le=2000)
    bedrooms: int = Field(ge=0, le=20)
    bathrooms: float = Field(ge=0, le=20)
    parking_spots: int = Field(ge=0, le=20)
    stratum: int = Field(ge=1, le=6)
    property_type: PropertyType
    year_built: Optional[int] = Field(default=None, ge=1900, le=2100)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    barrio_ideca: str = Field(min_length=1)
    property_id: Optional[uuid.UUID] = None


class PredictionResponse(StrictBase):
    id: uuid.UUID
    predicted_price: float
    model_version: str
    created_at: datetime


class BatchPredictionResult(StrictBase):
    predictions: list[tuple[uuid.UUID, float]]          # (property_id, predicted_price) — publicar al topic
    failed: list[tuple[uuid.UUID, PredictionRequest]]   # (property_id, req) — re-encolar


# class FeedbackRequest(StrictBase):
#     feedback: Feedback
