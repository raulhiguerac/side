import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from preprocessor import AVMPreprocessor


def load_and_preprocess(*, path: str, poi_path: str, schema: dict[str, Any]) -> tuple[pd.DataFrame, AVMPreprocessor, str]:
    poi_bytes = Path(poi_path).read_bytes()
    poi_md5 = hashlib.md5(poi_bytes).hexdigest()

    df = pd.read_csv(path)
    df_poi = pd.read_csv(poi_path)

    preprocessor = AVMPreprocessor(schema=schema)
    preprocessor.fit(poi_df=df_poi)

    target = schema["target"]
    df[target] = np.log10(df["price"])

    y = df[target].copy()
    df = preprocessor.transform_batch(records=df)
    df[target] = y

    return df, preprocessor, poi_md5


def validate(*, df: pd.DataFrame, schema: dict[str, Any]) -> pd.DataFrame:
    features = schema["features"]
    validations = schema["validations"]

    required_cols = features + [schema["target"]]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    target = schema["target"]
    if (df[target] <= 0).any():
        raise ValueError(f"{target} must be positive")

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
