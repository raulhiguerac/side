import uuid
import hashlib

def cache_key_forward_geocode(query: str, locality_id: uuid.UUID) -> str:
    raw = f"{query.strip().lower()}:{locality_id}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"geo:fwd:{digest}"


def cache_key_fetch_zone(h3_index: str) -> str:
    return f"geo:fetch_zone:{h3_index}"


def lock_key_fetch_zone(h3_index: str) -> str:
    return f"geo:fetch_zone:lock:{h3_index}"
