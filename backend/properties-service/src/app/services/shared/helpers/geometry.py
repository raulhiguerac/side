import h3
from geoalchemy2.shape import to_shape


def point_to_lat_lon(point) -> tuple[float, float]:
    """Extracts (latitude, longitude) from a GeoAlchemy2 POINT geometry."""
    shape = to_shape(point)
    return shape.y, shape.x


def compute_h3(lat: float, lng: float) -> tuple[str, str]:
    """Returns (h3_r9, h3_r7) index pair for a coordinate."""
    return h3.latlng_to_cell(lat, lng, 9), h3.latlng_to_cell(lat, lng, 7)
