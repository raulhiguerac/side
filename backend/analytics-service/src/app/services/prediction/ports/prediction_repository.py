from typing import Protocol

from app.models.prediction import Prediction

class PredictionRepository(Protocol):
    def add(self, *, record: Prediction) -> None: ...
    def batch_add(self, *, records: list[Prediction]) -> None: ...