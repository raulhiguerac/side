from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session

from app.models.prediction import Prediction
from app.services.prediction.ports.prediction_repository import PredictionRepository


class SqlPredictionRepository(PredictionRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, *, record: Prediction) -> None:
        self.session.add(record)
        self.session.flush()

    def batch_add(self, *, records: list[Prediction]) -> None:
        stmt = insert(Prediction).values([r.model_dump() for r in records]).on_conflict_do_nothing()
        self.session.execute(stmt)
