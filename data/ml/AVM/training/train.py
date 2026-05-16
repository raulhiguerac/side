import os
import itertools
import pandas as pd
import numpy as np
import lightgbm as lgb
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import warnings
import mlflow

from typing import Any
from schemas.types import DataSplit

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

FEATURES = [
    'area_m2_log', 'cuartos', 'banios', 'parqueaderos', 'estrato',
    'bedroom_m2', 'bathroom_bedroom', 'tipo_propiedad', 'antiguedad',
    'h3_r6', 'h3_r7', 'h3_r8', 'barrio_ideca'
]

CAT_COLS = ['h3_r6', 'h3_r7', 'h3_r8', 'barrio_ideca', 'antiguedad']

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    for col in ['h3_r6', 'h3_r7', 'h3_r8', 'barrio_ideca', 'antiguedad']:
        df[col] = df[col].astype('category')

    return df

def split_data(base_features: list[str], df: pd.DataFrame) -> DataSplit:
    poi_cols  = [c for c in df.columns if c.startswith('poi_')]
    dist_cols = [c for c in df.columns if c.startswith('dist_')]
    all_features = base_features + poi_cols + dist_cols

    X = df[all_features]
    y = df['price_log']

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=df['tipo_propiedad']
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=X_temp['tipo_propiedad']
    )

    return DataSplit(X_train, X_val, X_test, y_train, y_val, y_test)

def grid_search(
        *, 
        CAT_COLS: list[str], 
        X_train: pd.DataFrame, 
        y_train: pd.DataFrame, 
        X_val: pd.DataFrame, 
        y_val: pd.DataFrame
    ) -> dict[str, Any]:

    lgb_train = lgb.Dataset(
        X_train, y_train, categorical_feature=CAT_COLS, free_raw_data=False
    )
    lgb_eval = lgb.Dataset(X_val, y_val, categorical_feature=CAT_COLS, reference=lgb_train, free_raw_data=False)

    PARAM_GRID = {
        "boosting_type": ["gbdt", "rf"],
        "num_leaves":    [31, 63, 85, 127],
        "min_data_in_leaf": [30, 50, 100, 300, 400],
    }

    BASE_PARAMS = {
        "objective":          "regression",
        "metric":             "rmse",
        "learning_rate":      0.05,
        "feature_fraction":   0.9,
        "bagging_fraction":   0.8,
        "bagging_freq":       5,
        "verbose":            -1,
        "feature_pre_filter": False,
    }

    best_score = np.inf
    best_combo: dict[str, Any] = {}

    with mlflow.start_run(run_name="grid_search"):
        for combo in itertools.product(*PARAM_GRID.values()):
            with mlflow.start_run(nested=True):
                combo_params = dict(zip(PARAM_GRID.keys(), combo))
                
                model = lgb.train(
                    params={**BASE_PARAMS, **combo_params},
                    train_set=lgb_train,
                    num_boost_round=2000,
                    valid_sets=lgb_eval,
                    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
                )
            
                y_pred = model.predict(X_val)
                rmse   = np.sqrt(mean_squared_error(y_val, y_pred))

                mlflow.log_params(combo_params)
                mlflow.log_metric("rmse", rmse)

                if rmse < best_score:
                    best_score = rmse
                    best_combo = combo_params
    
    return best_combo

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
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=200, show_progress_bar=False)

        mlflow.log_params(study.best_params)
        mlflow.log_metric("best_rmse", study.best_value)

    return study.best_params


def final_train(*, best_params: dict[str, Any], split: DataSplit, CAT_COLS: list[str]) -> lgb.Booster:

    params = {
        **best_params,
        'objective': 'regression',
        'metric': 'rmse',
        'verbose': -1
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

        model = lgb.train(params, d_trainval, num_boost_round=best_rounds)

        y_pred = model.predict(split.X_test)
        rmse = np.sqrt(mean_squared_error(split.y_test, y_pred))
        mlflow.log_metric("test_rmse", rmse)

        mlflow.lightgbm.log_model(model, name="model", registered_model_name="avm-bogota-v1")

    return model

if __name__ == "__main__":
    uri = os.getenv("MLFLOW_TRACKING_URI")
    if not uri:
        raise ValueError("MLFLOW_TRACKING_URI not set")

    os.environ.setdefault("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "minioadmin")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "minioadmin")

    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment("avm-bogota-v1")

    df = load_data("data/model_ready.csv")
    split = split_data(FEATURES, df)

    best_params = tune_with_optuna(CAT_COLS=CAT_COLS, X_train=split.X_train, y_train=split.y_train, X_val=split.X_val, y_val=split.y_val)
    final_train(best_params=best_params, split=split, CAT_COLS=CAT_COLS)