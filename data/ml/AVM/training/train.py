import os
import json
import argparse
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split

from schemas.types import DataSplit
from pipeline.data import load_and_preprocess, validate
from pipeline.tuner import tune_with_optuna
from pipeline.trainer import final_train


def split_data(*, base_features: list[str], schema: dict[str, Any], df: pd.DataFrame) -> DataSplit:
    target = schema.get('target')

    X = df[base_features]
    y = df[target]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=df['tipo_propiedad']
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=X_temp['tipo_propiedad']
    )

    return DataSplit(X_train, X_val, X_test, y_train, y_val, y_test)


def run_train_pipeline(*, path: str, poi_path: str, schema: dict[str, Any], model_name: str):
    df, preprocessor, poi_md5 = load_and_preprocess(path=path, poi_path=poi_path, schema=schema)
    df = validate(df=df, schema=schema)
    split = split_data(base_features=schema["features"], schema=schema, df=df)

    best_params = tune_with_optuna(
        CAT_COLS=schema["cat_cols"],
        X_train=split.X_train,
        y_train=split.y_train,
        X_val=split.X_val,
        y_val=split.y_val,
    )
    final_train(
        best_params=best_params,
        split=split,
        CAT_COLS=schema["cat_cols"],
        schema=schema,
        model_name=model_name,
        preprocessor=preprocessor,
        poi_md5=poi_md5,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Train Bogota AVM')
    parser.add_argument('--data-path', required=True, help='Path to raw training csv with property columns plus price')
    parser.add_argument('--poi-path', required=True, help="Path to the POI's csv used to fit ball tree")
    parser.add_argument('--feature-schema-path', required=True, help='Path to the feature schema of the version')
    parser.add_argument('--experiment-name', required=True, help='MLflow experiment name')
    parser.add_argument('--model-name', required=True, help='MLflow model name')
    args = parser.parse_args()

    uri = os.getenv("MLFLOW_TRACKING_URI")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    mlflow_s3 = os.getenv("MLFLOW_S3_ENDPOINT_URL")

    missing = [k for k, v in {
        "MLFLOW_TRACKING_URI": uri,
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_access_key,
        "MLFLOW_S3_ENDPOINT_URL": mlflow_s3,
    }.items() if not v]
    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)}")

    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(args.experiment_name)
    os.environ["MLFLOW_RECORD_ENV_VARS_IN_MODEL_LOGGING"] = "false"

    TRAINING_DIR = Path(__file__).parent

    with open(TRAINING_DIR / args.feature_schema_path) as f:
        schema = json.load(f)

    run_train_pipeline(path=args.data_path, poi_path=args.poi_path, schema=schema, model_name=args.model_name)
