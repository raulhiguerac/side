from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import haversine_distances

from feature_store.constants import BOGOTA_LANDMARKS


def add_landmark_distances(df: pd.DataFrame) -> pd.DataFrame:
    """Add dist_{landmark} columns in km via haversine for each listing row."""
    coords_listings = np.radians(df[['lat', 'lon']].values)

    for name, coords in BOGOTA_LANDMARKS.items():
        landmark = np.radians([[coords['lat'], coords['lon']]])
        dist_rad  = haversine_distances(coords_listings, landmark)
        df[f'dist_{name}'] = dist_rad * 6371.0

    return df
