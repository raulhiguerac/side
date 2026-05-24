import asyncio

from sqlmodel import Session

from app.db import engine
from app.integrations.ml.mlflow.model import ModelClient
from app.services.prediction.adapters.avm_model_adapter import AVMModelAdapter
from app.services.prediction.adapters.sql_prediction_unit_of_work import SqlPredictionUnitOfWork
from app.services.prediction.use_cases.batch import BatchPrediction
from app.workers.listing_created.consumer import ListingConsumer


class ListingWorkerRunner:
    def __init__(self) -> None:
        model_client = ModelClient()
        self.model = AVMModelAdapter(client=model_client)

    async def run(self) -> None: 
        with Session(engine) as session:
            uow = SqlPredictionUnitOfWork(session=session)

            uc = BatchPrediction(
                uow=uow,
                model=self.model
            )

            kafka_consumer = ListingConsumer(uc=uc)

            with kafka_consumer:
                while True:
                    await kafka_consumer.consume_batch()
                    await asyncio.sleep(900)
