import uuid
from functools import partial
from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.prediction import PredictionPersistenceError
from app.models.prediction import Prediction, SourceType
from app.services.prediction.ports.model_gateway import ModelGateway
from app.services.prediction.ports.unit_of_work import PredictionUnitOfWork
from app.services.prediction.schemas.prediction import PredictionRequest, PredictionResponse


class OnlinePrediction:
    def __init__(self, *, uow: PredictionUnitOfWork, model: ModelGateway) -> None:
        self.uow = uow
        self.model = model

    @staticmethod
    def create_record(
        *,
        req: PredictionRequest,
        predicted_price: float,
        model_version: str,
        created_by: uuid.UUID,
    ) -> Prediction:
        return Prediction(
            area_m2=req.area_m2,
            bedrooms=req.bedrooms,
            bathrooms=req.bathrooms,
            parking_spots=req.parking_spots,
            stratum=req.stratum,
            property_type=req.property_type,
            year_built=req.year_built,
            lat=req.lat,
            lon=req.lon,
            barrio_ideca=req.barrio_ideca,
            property_id=req.property_id,
            predicted_price=predicted_price,
            model_version=model_version,
            source=SourceType.online,
            created_by=created_by,
            updated_by=created_by,
        )

    async def execute(self, *, principal: uuid.UUID, req: PredictionRequest) -> PredictionResponse:
        predicted_price, model_version = await run_in_threadpool(
            partial(self.model.online_predict, record=req)
        )

        db_record = self.create_record(
            req=req,
            predicted_price=predicted_price,
            model_version=model_version,
            created_by=principal,
        )

        try:
            self.uow.prediction.add(record=db_record)
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise PredictionPersistenceError(cause=exc) from exc

        return PredictionResponse(
            id=db_record.id,
            predicted_price=db_record.predicted_price,
            model_version=db_record.model_version,
            created_at=db_record.created_at,
        )
