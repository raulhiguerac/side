from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from feature_store.constants import (
    AMENITY_MAP,
    HEALTHCARE_MAP,
    LEISURE_MAP,
    POI_RADII_KM,
    PUBLIC_TRANSPORT_MAP,
    SHOP_MAP,
)


def map_to_category(d: dict[str, list[str]]) -> dict[str, str]:
    return {v: cat for cat, values in d.items() for v in values}


class PoiTransformer:

    def __init__(self) -> None:
        self.tree: BallTree | None = None
        self.poi_categories: np.ndarray | None = None
        self.poi_category_names: list[str] = []

    def fit(self, poi_df: pd.DataFrame) -> PoiTransformer:
        """Assign categories, build BallTree, store category array."""
        df = poi_df.copy()

        df['category'] = (
            df['amenity'].map(map_to_category(AMENITY_MAP))
            .fillna(df['shop'].map(map_to_category(SHOP_MAP)))
            .fillna(df['public_transport'].map(map_to_category(PUBLIC_TRANSPORT_MAP)))
            .fillna(df['leisure'].map(map_to_category(LEISURE_MAP)))
            .fillna(df['healthcare'].map(map_to_category(HEALTHCARE_MAP)))
        )

        df = df[df['category'].notna()]

        uncategorized = poi_df.shape[0] - df.shape[0]
        print(f"POIs sin categoría: {uncategorized} ({uncategorized / len(poi_df) * 100:.1f}%)")

        if df.empty:
            raise ValueError("No POIs could be categorized")

        coords_pois = np.radians(df[['lat', 'lon']].values)
        self.tree = BallTree(coords_pois, metric='haversine')
        self.poi_categories = df['category'].values
        self.poi_category_names = sorted(df['category'].unique())
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add poi_{radius}m_{category} count columns for each listing row."""
        if self.tree is None or self.poi_categories is None:
            raise RuntimeError("PoiTransformer must be fitted before calling transform")

        coords_listings = np.radians(df[['lat', 'lon']].values)

        for km in POI_RADII_KM:
            radius_rad    = km / 6371.0
            indices       = self.tree.query_radius(coords_listings, r=radius_rad)
            expected_cols = [f"poi_{int(km * 1000)}m_{cat}" for cat in self.poi_category_names]
            match_counts  = [len(i) for i in indices]

            if sum(match_counts) == 0:
                poi_features = pd.DataFrame(0, index=np.arange(len(df)), columns=expected_cols)
            else:
                listing_idx = np.repeat(np.arange(len(df)), match_counts)
                poi_idx     = np.concatenate(indices)

                pairs = pd.DataFrame({
                    'listing_idx': listing_idx,
                    'category':    self.poi_categories[poi_idx],
                })

                poi_features = (
                    pairs.groupby(['listing_idx', 'category'])
                    .size()
                    .unstack(fill_value=0)
                    .add_prefix(f'poi_{int(km * 1000)}m_')
                    .reindex(index=np.arange(len(df)), columns=expected_cols, fill_value=0)
                )

            poi_features.index = df.index
            df = df.join(poi_features)

        return df
