from typing import Any

from shapely.geometry import mapping, shape
from geoalchemy2.shape import from_shape, to_shape


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
