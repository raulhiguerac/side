import tempfile
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import pandas as pd
import lightgbm as lgb
from mlflow.models import infer_signature
from sklearn.metrics import mean_squared_error

from preprocessor import AVMPreprocessor
from schemas.types import DataSplit
from avm_model import AVM

SEED = 42


def _make_raw_input_example() -> pd.DataFrame:
    return pd.DataFrame([{
        "area_m2": 72.0,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "parking_spots": 1,
        "stratum": 4,
        "property_type": "apartment",
        "year_built": 2012,
        "lat": 4.65,
        "lon": -74.08,
        "barrio_ideca": "CHICO NORTE",
    }])


def final_train(
        *,
        best_params: dict[str, Any],
        split: DataSplit,
        CAT_COLS: list[str],
        schema: dict[str, Any],
        model_name: str,
        preprocessor: AVMPreprocessor,
        poi_md5: str,
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

        mlflow.log_param("train_size", len(split.X_train))
        mlflow.log_param("val_size", len(split.X_val))
        mlflow.log_param("test_size", len(split.X_test))

        all_features = list(split.X_train.columns)
        mlflow.log_param("n_features", len(all_features))
        mlflow.log_param("n_poi_features", sum(1 for c in all_features if c.startswith("poi_")))
        mlflow.log_param("n_dist_features", sum(1 for c in all_features if c.startswith("dist_")))

        mlflow.log_metric("target_mean", split.y_train.mean())
        mlflow.log_metric("target_std", split.y_train.std())
        mlflow.log_metric("target_min", float(split.y_train.min()))
        mlflow.log_metric("target_max", float(split.y_train.max()))

        mlflow.log_param("poi_md5", poi_md5)
        mlflow.log_dict(schema, "feature_schema.json")

        model = lgb.train(params, d_trainval, num_boost_round=best_rounds)

        y_pred = model.predict(split.X_test)
        rmse = np.sqrt(mean_squared_error(split.y_test, y_pred))
        y_pred_real = 10 ** y_pred
        y_test_real = 10 ** split.y_test
        mape = np.mean(np.abs((y_test_real - y_pred_real) / y_test_real)) * 100
        mlflow.log_metric("test_rmse", rmse)
        mlflow.log_metric("test_mape", mape)

        input_example = _make_raw_input_example()

        signature = infer_signature(
            input_example,
            pd.Series([500_000_000.0], name="price"),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            preprocessor_path = Path(tmpdir) / "preprocessor.pkl"
            model_path = Path(tmpdir) / "booster.txt"

            preprocessor.save(preprocessor_path)
            model.save_model(str(model_path))

            mlflow.pyfunc.log_model(
                name="avm",
                registered_model_name=model_name,
                python_model=AVM(),
                artifacts={
                    "preprocessor": str(preprocessor_path),
                    "booster": str(model_path),
                },
                code_paths=[
                    str(Path(__file__).parents[1] / "avm_model.py"),
                    str(Path(__file__).parents[1] / "preprocessor.py"),
                    str(Path(__file__).parents[1] / "transforms"),
                    str(Path(__file__).parents[1] / "feature_store"),
                ],
                input_example=input_example,
                signature=signature,
            )

    return model
