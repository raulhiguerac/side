import uuid


def cache_key_poi(poi_id: uuid.UUID) -> str:
    return f"catalog:poi:{poi_id}"


def cache_key_pois_by_locality(locality_id: uuid.UUID) -> str:
    return f"catalog:locality:{locality_id}:pois"


def cache_key_poi_by_mapbox_id(mapbox_id: str) -> str:
    return f"catalog:poi:mapbox:{mapbox_id}"
