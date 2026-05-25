import os
import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from typing import Any


class ModelClient:
    def __init__(self):
        uri = os.getenv("MLFLOW_TRACKING_URI")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        mlflow_s3 = os.getenv("MLFLOW_S3_ENDPOINT_URL")
        model_uri = os.getenv("MLFLOW_MODEL_URI")

        missing = [k for k, v in {
            "MLFLOW_TRACKING_URI": uri,
            "AWS_ACCESS_KEY_ID": access_key,
            "AWS_SECRET_ACCESS_KEY": secret_access_key,
            "MLFLOW_S3_ENDPOINT_URL": mlflow_s3,
            "MLFLOW_MODEL_URI": model_uri
        }.items() if not v]
        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")

        mlflow.set_tracking_uri(uri)
        self._mlflow_client = MlflowClient()
        self._model = mlflow.pyfunc.load_model(model_uri)

    def get_version(self, *, model_name: str, alias: str) -> str:
        return self._mlflow_client.get_model_version_by_alias(model_name, alias).version

    def online_predict(self, *, record: dict[str, Any]) -> float:
        df = pd.DataFrame([record])
        return self._model.predict(df).iloc[0]
    
    def batch_predict(self, *, records: list[dict[str, Any]]) -> list[float]:
        df = pd.DataFrame(records)
        return self._model.predict(df).tolist()