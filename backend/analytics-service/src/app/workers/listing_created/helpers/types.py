import uuid
from typing import TypedDict
from app.services.prediction.schemas.prediction import PredictionRequest

class WorkerMessage(TypedDict):
    id: uuid.UUID
    attempts: int
    request: PredictionRequest