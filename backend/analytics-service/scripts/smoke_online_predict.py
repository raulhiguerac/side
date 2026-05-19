"""
Smoke test for OnlinePrediction UC with real MLflow model, no DB.

Usage (from analytics-service root):
    export $(cat .env | xargs)
    uv run python scripts/smoke_online_predict.py
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

from app.integrations.ml.mlflow.model import ModelClient
from app.services.prediction.adapters.avm_model_adapter import AVMModelAdapter
from app.services.prediction.schemas.prediction import PredictionRequest
from app.services.prediction.use_cases.online import OnlinePrediction


def build_uow() -> MagicMock:
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.prediction.add = MagicMock()
    return uow


async def main() -> None:
    client = ModelClient()
    model = AVMModelAdapter(client=client)
    uc = OnlinePrediction(uow=build_uow(), model=model)

    req = PredictionRequest(
        area_m2=80.0,
        bedrooms=3,
        bathrooms=2.0,
        parking_spots=1,
        stratum=3,
        property_type="apartment",
        year_built=2005,
        lat=4.6097,
        lon=-74.0817,
        barrio_ideca="CHAPINERO",
    )

    result = await uc.execute(principal=uuid.uuid4(), req=req)
    print(f"predicted_price : {result.predicted_price:,.0f}")
    print(f"model_version   : {result.model_version}")
    print(f"prediction_id   : {result.id}")


if __name__ == "__main__":
    asyncio.run(main())
