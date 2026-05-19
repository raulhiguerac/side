import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import DateTime, Index
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel

class AuditMixin(SQLModel):
    """Campos de auditoría para todas las entidades."""

    created_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now(), "nullable": False},
    )
    created_by: Optional[uuid.UUID] = Field(default=None)
    updated_by: Optional[uuid.UUID] = Field(default=None)

class PropertyType(str, Enum):
    apartment = "apartment"
    house = "house"

class SourceType(str, Enum):
    batch = "batch"
    online = "online"

class PredictionFeedback(str, Enum):
    muy_mal  = "muy_mal"
    mal      = "mal"
    regular  = "regular"
    bien     = "bien"
    muy_bien = "muy_bien"


class Prediction(AuditMixin, table=True):

    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_model_version", "model_version"),
        Index("ix_predictions_created_at", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    area_m2: float
    bedrooms: int
    bathrooms: float
    parking_spots: int
    stratum: int
    property_type: PropertyType
    year_built: Optional[int] = Field(default=None)
    lat: float
    lon: float
    barrio_ideca: str

    property_id: Optional[uuid.UUID] = Field(default=None)

    predicted_price: float
    model_version: str

    source: SourceType
    feedback: Optional[PredictionFeedback] = Field(default=None)
    feedback_comment: Optional[str] = Field(default=None)
