from app.integrations.ml.mlflow.model import ModelClient
from app.services.prediction.schemas.prediction import PredictionRequest


class AVMModelAdapter:
    def __init__(self, *, client: ModelClient) -> None:
        self.client = client

    def online_predict(self, *, record: PredictionRequest) -> tuple[float, str]:
        version = self.client.get_version(model_name="bogota-avm", alias="production")
        price = self.client.online_predict(record=record.model_dump(mode='json', exclude={'property_id'}))
        return price, version

    # def batch_predict(self, *, records: list[PredictionRequest]) -> tuple[list[float], str]:
    #     version = self.mlflow_client.get_model_version_by_alias("bogota-avm", "production")
    #     prices = self.client.batch_predict(records=[r.model_dump(mode='json', exclude={'property_id'}) for r in records])
    #     return prices, version.version
