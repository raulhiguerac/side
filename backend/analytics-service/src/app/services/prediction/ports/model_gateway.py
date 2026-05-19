from typing import Protocol

from app.services.prediction.schemas.prediction import PredictionRequest


class ModelGateway(Protocol):
    def online_predict(self, *, record: PredictionRequest) -> tuple[float, str]: ...
    def batch_predict(self, *, records: list[PredictionRequest]) -> tuple[list[float], str]: ...
