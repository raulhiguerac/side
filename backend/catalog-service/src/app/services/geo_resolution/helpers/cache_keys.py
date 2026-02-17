import uuid
import hashlib


def cache_key_forward_geocode(query: str, locality_id: uuid.UUID) -> str:
    raw = f"{query.strip().lower()}:{locality_id}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"geo:fwd:{digest}"


def cache_key_poi(poi_id: uuid.UUID) -> str:
    return f"catalog:poi:{poi_id}"


def cache_key_pois_by_locality(locality_id: uuid.UUID) -> str:
    return f"catalog:locality:{locality_id}:pois"


def cache_key_poi_by_external_id(external_id: str, source: str) -> str:
    return f"catalog:poi:{source}:{external_id}"
