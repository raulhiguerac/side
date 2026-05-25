import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.prediction import PredictionPersistenceError
from app.core.logging.logger import get_logger
from app.models.prediction import SourceType
from app.services.prediction.helpers.record_builder import build_prediction_record
from app.services.prediction.ports.model_gateway import ModelGateway
from app.services.prediction.ports.unit_of_work import PredictionUnitOfWork
from app.services.prediction.schemas.prediction import PredictionRequest, PredictionResponse

logger = get_logger(__name__)


class OnlinePrediction:
    def __init__(self, *, uow: PredictionUnitOfWork, model: ModelGateway) -> None:
        self.uow = uow
        self.model = model

    async def execute(self, *, principal: uuid.UUID, req: PredictionRequest) -> PredictionResponse:
        predicted_price, model_version = await run_in_threadpool(
            partial(self.model.online_predict, record=req)
        )

        db_record = build_prediction_record(
            req=req,
            predicted_price=predicted_price,
            model_version=model_version,
            created_by=principal,
            source=SourceType.online,
        )

        try:
            await run_in_threadpool(partial(self.uow.prediction.add, record=db_record))
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            logger.error("prediction_persistence_failed", exc_info=exc)
            raise PredictionPersistenceError(cause=exc) from exc

        return PredictionResponse(
            id=db_record.id,
            predicted_price=db_record.predicted_price,
            model_version=db_record.model_version,
            created_at=db_record.created_at,
        )
