from fastapi import APIRouter, Depends, status

from app.api.deps.auth import get_current_principal
from app.api.deps.prediction import get_online_prediction_uc
from app.schemas.principal import Principal
from app.services.prediction.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction.use_cases.online import OnlinePrediction

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def predict(
    req: PredictionRequest,
    principal: Principal = Depends(get_current_principal),
    uc: OnlinePrediction = Depends(get_online_prediction_uc),
) -> PredictionResponse:
    return await uc.execute(principal=principal.sub, req=req)
