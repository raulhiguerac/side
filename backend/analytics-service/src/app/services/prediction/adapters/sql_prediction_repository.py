from sqlmodel import Session, select

from app.models.prediction import Prediction

from app.services.prediction.ports.prediction_repository import PredictionRepository

class SqlPredictionRepository(PredictionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def add(self, *, record: Prediction) -> None:
        self.session.add(record)
        self.session.flush()