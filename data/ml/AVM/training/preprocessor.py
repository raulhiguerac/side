from __future__ import annotations

import joblib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from transforms import (
    add_h3,
    add_landmark_distances,
    cast_categoricals,
    encode_base_features,
    PoiTransformer,
)


@dataclass
class RawPropertyInput:
    area_m2: float
    bedrooms: int
    bathrooms: float
    parking_spots: int
    stratum: int
    property_type: str       # "apartment" | "house"
    year_built: Optional[int]
    lat: float
    lon: float
    barrio_ideca: str        # resolved from neighborhood_id via catalog-service


class AVMPreprocessor:

    def __init__(self, schema: dict) -> None:
        self.cat_cols = schema["cat_cols"]
        self.features = schema["features"]
        self.poi_transformer = PoiTransformer()

    def fit(self, poi_df: pd.DataFrame) -> AVMPreprocessor:
        """Build BallTree from POI coordinates and store category metadata."""
        self.poi_transformer.fit(poi_df)
        return self

    def transform(self, prop: RawPropertyInput) -> pd.Series:
        """Single-record inference — returns a Series with the 70 model features."""
        return self.transform_batch([prop]).iloc[0]

    def transform_batch(self, records: list[RawPropertyInput] | pd.DataFrame) -> pd.DataFrame:
        """Batch inference — BallTree and haversine run vectorized over all records."""
        if isinstance(records, pd.DataFrame):
            df = records.copy()
        else:
            df = pd.DataFrame([vars(p) for p in records])
        df = encode_base_features(df)
        df = add_h3(df)
        df = self.poi_transformer.transform(df)
        df = add_landmark_distances(df)
        df = cast_categoricals(df, self.cat_cols)
        return df[self.features]

    def save(self, path: str | Path) -> None:
        """Serialize preprocessor state to disk with joblib."""
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> AVMPreprocessor:
        """Deserialize preprocessor from disk."""
        return joblib.load(path)
