import asyncio

from sqlmodel import Session

from app.core.logging.logger import get_logger, setup_logging
from app.db import engine
from app.integrations.ml.mlflow.model import ModelClient
from app.services.prediction.adapters.avm_model_adapter import AVMModelAdapter
from app.services.prediction.adapters.sql_prediction_unit_of_work import SqlPredictionUnitOfWork
from app.services.prediction.use_cases.batch import BatchPrediction
from app.workers.listing_created.consumer import ListingConsumer

logger = get_logger(__name__)


class ListingWorkerRunner:
    def __init__(self) -> None:
        logger.info("worker_init_start")
        model_client = ModelClient()
        self.model = AVMModelAdapter(client=model_client)
        logger.info("worker_init_done")

    async def run(self) -> None:
        logger.info("worker_run_start")
        try:
            with Session(engine) as session:
                uow = SqlPredictionUnitOfWork(session=session)
                uc = BatchPrediction(uow=uow, model=self.model)
                kafka_consumer = ListingConsumer(uc=uc)

                with kafka_consumer:
                    while True:
                        logger.info("worker_batch_cycle_start")
                        await kafka_consumer.consume_batch()
                        logger.info("worker_batch_cycle_done")
                        await asyncio.sleep(900)
        except Exception:
            logger.exception("worker_fatal_error")
            raise


if __name__ == "__main__":
    setup_logging()
    asyncio.run(ListingWorkerRunner().run())
