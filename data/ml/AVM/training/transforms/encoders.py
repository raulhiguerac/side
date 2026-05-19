from __future__ import annotations

from typing import Optional

import h3
import numpy as np
import pandas as pd

from feature_store.constants import (
    ANTIGUEDAD_BINS,
    ANTIGUEDAD_LABELS,
    H3_RESOLUTIONS,
    PROPERTY_TYPE_MAP,
    RENAME_MAP,
)


def _year_to_antiguedad(year_built: Optional[int]) -> str:
    if year_built is None or pd.isna(year_built):
        return 'sin especificar'
    age = pd.Timestamp.now().year - year_built
    for i, limit in enumerate(ANTIGUEDAD_BINS[1:]):
        if age < limit:
            return ANTIGUEDAD_LABELS[i]
    return ANTIGUEDAD_LABELS[-1]


def encode_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns, compute derived features, encode categoricals."""
    df = df.rename(columns=RENAME_MAP)

    df['antiguedad']       = df['year_built'].apply(_year_to_antiguedad)
    df['area_m2_log']      = np.log10(df['area_m2'])
    df['bedroom_m2']       = df['cuartos'] / df['area_m2']
    df['bathroom_bedroom'] = df['banios'] / df['cuartos'].replace(0, np.nan)
    df['tipo_propiedad']   = df['tipo_propiedad'].map(PROPERTY_TYPE_MAP)
    df['estrato']          = df['estrato'].astype(int)

    return df


def add_h3(df: pd.DataFrame) -> pd.DataFrame:
    """Add h3_r6, h3_r7, h3_r8 columns from lat/lon."""
    for res in H3_RESOLUTIONS:
        df[f'h3_r{res}'] = df.apply(
            lambda row, r=res: h3.latlng_to_cell(row['lat'], row['lon'], r), axis=1
        )
    return df


def cast_categoricals(df: pd.DataFrame, cat_cols: list[str]) -> pd.DataFrame:
    """Cast cat_cols to pandas Categorical dtype."""
    for col in cat_cols:
        df[col] = df[col].astype('category')
    return df
