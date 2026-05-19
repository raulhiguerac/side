from typing import Any

import mlflow
import numpy as np
import lightgbm as lgb
import optuna
from optuna.samplers import TPESampler
from sklearn.metrics import mean_squared_error
import pandas as pd

SEED = 42

optuna.logging.set_verbosity(optuna.logging.WARNING)


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
