import os
import json
import argparse
from pathlib import Path
from typing import Any

import optuna
import mlflow
import numpy as np
import pandas as pd
import lightgbm as lgb
from mlflow.models import infer_signature
from optuna.samplers import TPESampler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from schemas.types import DataSplit

optuna.logging.set_verbosity(optuna.logging.WARNING)

SEED = 42

def load_data(*, path: str, schema: dict[str, Any]) -> pd.DataFrame:
    df = pd.read_csv(path)

    for col in schema.get("cat_cols"):
        df[col] = df[col].astype('category')

    return df

def validate(*, df: pd.DataFrame, schema: dict[str, Any]) -> pd.DataFrame:
    features = schema["features"]
    validations = schema["validations"]

    required_cols = features + [schema["target"]]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    if len(df.columns) != validations["number_cols"]:
        raise ValueError(f"Expected {validations['number_cols']} columns, got {len(df.columns)}")

    null_pct = df[required_cols].isnull().mean()
    high_null = null_pct[null_pct > 0]
    if not high_null.empty:
        raise ValueError(f"Columns with nulls: {high_null.to_dict()}")

    estrato_rules = validations["estrato"]
    if not df["estrato"].between(estrato_rules["min"], estrato_rules["max"]).all():
        raise ValueError(f"estrato out of range [{estrato_rules['min']}, {estrato_rules['max']}]")

    if (df["area_m2_log"] <= validations["area_m2_log"]["min_exclusive"]).any():
        raise ValueError("area_m2_log has non-positive values")

    return df
    

def split_data(
        *, 
        base_features: list[str], 
        schema: dict[str,Any], 
        df: pd.DataFrame
    ) -> DataSplit:
    
    all_features = base_features
    target = schema.get('target')

    X = df[all_features]
    y = df[target]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=df['tipo_propiedad']
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=X_temp['tipo_propiedad']
    )

    return DataSplit(X_train, X_val, X_test, y_train, y_val, y_test)

def tune_with_optuna(
        *,
        CAT_COLS: list[str],
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
    ) -> dict[str, Any]:

    lgb_train = lgb.Dataset(X_train, y_train, categorical_feature=CAT_COLS, free_raw_data=False)
    lgb_eval = lgb.Dataset(X_val, y_val, categorical_feature=CAT_COLS, reference=lgb_train, free_raw_data=False)

    def objective(trial) -> float:
        params = {
            'objective':          'regression',
            'metric':             'rmse',
            'verbose':            -1,
            'feature_pre_filter': False,
            'seed':               SEED,
            'feature_fraction_seed': SEED,
            'bagging_seed':       SEED,
            'data_random_seed':   SEED,
            'num_leaves':         trial.suggest_int('num_leaves', 31, 255),
            'learning_rate':     trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
            'max_depth':         trial.suggest_int('max_depth', 4, 12),
            'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
            'feature_fraction':  trial.suggest_float('feature_fraction', 0.5, 1.0),
            'bagging_fraction':  trial.suggest_float('bagging_fraction', 0.5, 1.0),
            'bagging_freq':      trial.suggest_int('bagging_freq', 1, 7),
            'reg_alpha':         trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
            'reg_lambda':        trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        }

        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=2000,
            valid_sets=[lgb_eval],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
        )

        y_pred = model.predict(X_val)
        return np.sqrt(mean_squared_error(y_val, y_pred))

    with mlflow.start_run(run_name='optuna_fine_tuning'):
        study = optuna.create_study(direction='minimize', sampler=TPESampler(seed=SEED))
        study.optimize(objective, n_trials=400, show_progress_bar=False)

        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_rmse", study.best_value)

    return study.best_params


def final_train(
        *, 
        best_params: dict[str, Any], 
        split: DataSplit, 
        CAT_COLS: list[str], 
        schema: dict[str, Any], 
        model_name: str
    ) -> lgb.Booster:

    params = {
        **best_params,
        'objective':          'regression',
        'metric':             'rmse',
        'verbose':            -1,
        'seed':               SEED,
        'feature_fraction_seed': SEED,
        'bagging_seed':       SEED,
        'data_random_seed':   SEED,
    }

    lgb_train = lgb.Dataset(split.X_train, split.y_train, categorical_feature=CAT_COLS, free_raw_data=False)
    lgb_eval = lgb.Dataset(split.X_val, split.y_val, categorical_feature=CAT_COLS, reference=lgb_train, free_raw_data=False)

    tuned_val = lgb.train(
        params,
        lgb_train,
        num_boost_round=2000,
        valid_sets=[lgb_eval],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
    )
    best_rounds = tuned_val.best_iteration

    X_trainval = pd.concat([split.X_train, split.X_val])
    y_trainval = pd.concat([split.y_train, split.y_val])
    d_trainval = lgb.Dataset(X_trainval, label=y_trainval, categorical_feature=CAT_COLS)

    with mlflow.start_run(run_name="final_model"):
        mlflow.log_params(params)
        mlflow.log_param("best_rounds", best_rounds)

        # dataset sizes
        mlflow.log_param("train_size", len(split.X_train))
        mlflow.log_param("val_size", len(split.X_val))
        mlflow.log_param("test_size", len(split.X_test))

        # feature breakdown
        all_features = list(split.X_train.columns)
        mlflow.log_param("n_features", len(all_features))
        mlflow.log_param("n_poi_features", sum(1 for c in all_features if c.startswith("poi_")))
        mlflow.log_param("n_dist_features", sum(1 for c in all_features if c.startswith("dist_")))

        # target distribution
        mlflow.log_metric("target_mean", split.y_train.mean())
        mlflow.log_metric("target_std", split.y_train.std())
        mlflow.log_metric("target_min", float(split.y_train.min()))
        mlflow.log_metric("target_max", float(split.y_train.max()))

        # schema
        mlflow.log_dict(schema, "feature_schema.json")

        model = lgb.train(params, d_trainval, num_boost_round=best_rounds)

        y_pred = model.predict(split.X_test)
        rmse = np.sqrt(mean_squared_error(split.y_test, y_pred))
        y_pred_real = 10 ** y_pred
        y_test_real = 10 ** split.y_test
        mape = np.mean(np.abs((y_test_real - y_pred_real) / y_test_real)) * 100
        mlflow.log_metric("test_rmse", rmse)
        mlflow.log_metric("test_mape", mape)

        signature = infer_signature(split.X_train, model.predict(split.X_train))
        mlflow.lightgbm.log_model(
            model,
            name="model",
            registered_model_name=model_name,
            signature=signature,
            input_example=split.X_train.iloc[[0]],
        )

    return model

def run_train_pipeline(*, path: str, schema: dict[str, Any], model_name: str):
    df = load_data(path=path, schema=schema)
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
        split=split, CAT_COLS=schema["cat_cols"], 
        schema=schema, 
        model_name=model_name
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Train Bogota AVM')
    parser.add_argument('--data-path', required=True, help='Path to model_ready.csv')
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

    TRAINING_DIR = Path(__file__).parent

    with open(TRAINING_DIR / args.feature_schema_path) as f:
        schema = json.load(f)

    run_train_pipeline(path=args.data_path, schema=schema, model_name=args.model_name)
