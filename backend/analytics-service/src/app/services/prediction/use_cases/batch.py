import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.logging.logger import get_logger
from app.models.prediction import SourceType
from app.services.prediction.helpers.record_builder import build_prediction_record
from app.services.prediction.ports.model_gateway import ModelGateway
from app.services.prediction.ports.unit_of_work import PredictionUnitOfWork
from app.services.prediction.schemas.prediction import BatchPredictionResult, PredictionRequest

logger = get_logger(__name__)


class BatchPrediction:
    def __init__(self, *, uow: PredictionUnitOfWork, model: ModelGateway) -> None:
        self.uow = uow
        self.model = model

    async def execute(
        self,
        *,
        principal: uuid.UUID,
        messages: list[tuple[uuid.UUID, PredictionRequest]],
    ) -> BatchPredictionResult:
        ids = [msg_id for msg_id, _ in messages]
        reqs = [req for _, req in messages]

        predicted_prices, model_version = await run_in_threadpool(
            partial(self.model.batch_predict, records=reqs)
        )

        db_records = [
            build_prediction_record(
                req=req,
                predicted_price=predicted_prices[idx],
                model_version=model_version,
                created_by=principal,
                source=SourceType.batch,
            )
            for idx, req in enumerate(reqs)
        ]

        try:
            await run_in_threadpool(partial(self.uow.prediction.batch_add, records=db_records))
            await self.uow.commit()
            return BatchPredictionResult(
                predictions=[(msg_id, r.predicted_price) for msg_id, r in zip(ids, db_records)],
                failed=[],
            )
        except Exception as exc:
            await self.uow.rollback()
            logger.warning("batch_insert_failed_falling_back", exc_info=exc)

        predictions: list[tuple[uuid.UUID, float]] = []
        failed: list[tuple[uuid.UUID, PredictionRequest]] = []

        for msg_id, req, db_record in zip(ids, reqs, db_records):
            try:
                await self.uow.begin_nested()
                await run_in_threadpool(partial(self.uow.prediction.add, record=db_record))
                predictions.append((msg_id, db_record.predicted_price))
            except Exception as exc:
                await self.uow.rollback_to_savepoint()
                logger.warning(
                    "batch_record_insert_failed",
                    extra={"property_id": str(msg_id)},
                    exc_info=exc,
                )
                failed.append((msg_id, req))

        if predictions:
            await self.uow.commit()

        return BatchPredictionResult(predictions=predictions, failed=failed)
