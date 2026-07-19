from typing import Any

import h3
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape


def geom_to_geojson(geom) -> dict[str, Any] | None:
    """Converts a GeoAlchemy2 WKBElement to a GeoJSON dict."""
    if geom is None:
        return None
    return dict(mapping(to_shape(geom)))


def geom_from_geojson(geojson: dict[str, Any] | None):
    """Converts a GeoJSON dict back to a GeoAlchemy2 WKBElement (srid=4326)."""
    if geojson is None:
        return None
    return from_shape(shape(geojson), srid=4326)


def h3_cells_for_geojson(geojson: dict[str, Any], *, resolution: int) -> list[str]:
    """H3 cells (by centroid) covering a GeoJSON Polygon/MultiPolygon."""
    return list(h3.geo_to_cells(geojson, resolution))
