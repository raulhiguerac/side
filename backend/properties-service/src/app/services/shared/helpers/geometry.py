from geoalchemy2.shape import to_shape


def point_to_lat_lon(point) -> tuple[float, float]:
    """Extracts (latitude, longitude) from a GeoAlchemy2 POINT geometry."""
    shape = to_shape(point)
    return shape.y, shape.x
