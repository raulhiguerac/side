from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.integrations.ml.mlflow.model import ModelClient
from app.services.prediction.adapters.avm_model_adapter import AVMModelAdapter
from app.services.prediction.adapters.sql_prediction_unit_of_work import SqlPredictionUnitOfWork
from app.services.prediction.ports.unit_of_work import PredictionUnitOfWork
from app.services.prediction.use_cases.online import OnlinePrediction


# -------------------------------------------------------------------------
# Stateless providers (singleton — safe to cache at module level)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_model_client() -> ModelClient:
    return ModelClient()


@lru_cache(maxsize=1)
def get_model_adapter() -> AVMModelAdapter:
    return AVMModelAdapter(client=get_model_client())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> PredictionUnitOfWork:
    return SqlPredictionUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_online_prediction_uc(
    uow: PredictionUnitOfWork = Depends(get_uow),
    model: AVMModelAdapter = Depends(get_model_adapter),
) -> OnlinePrediction:
    return OnlinePrediction(uow=uow, model=model)
