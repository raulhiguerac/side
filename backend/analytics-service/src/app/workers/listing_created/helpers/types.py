import uuid

from pydantic import Field

from app.schemas.base import StrictBase
from app.services.prediction.schemas.prediction import PredictionRequest


class WorkerMessage(StrictBase):
    id: uuid.UUID
    attempts: int = Field(default=1, ge=1, strict=True)
    model: PredictionRequest
