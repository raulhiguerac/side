import uuid

from app.models.prediction import Prediction, SourceType
from app.services.prediction.schemas.prediction import PredictionRequest


def build_prediction_record(
    *,
    req: PredictionRequest,
    predicted_price: float,
    model_version: str,
    created_by: uuid.UUID,
    source: SourceType,
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
        source=source,
        created_by=created_by,
        updated_by=created_by,
    )
