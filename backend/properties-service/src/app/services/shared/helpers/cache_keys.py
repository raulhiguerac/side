import hashlib
import json
import uuid
from typing import Any


def _short_hash(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def client_properties(user_id: uuid.UUID) -> str:
    return f"properties:user:{user_id}"


def public_user_properties(user_id: uuid.UUID, offset: int = 0) -> str:
    return f"properties:user:{user_id}:public:{offset}"


def public_user_properties_pattern(user_id: uuid.UUID) -> str:
    return f"properties:user:{user_id}:public:*"


def cache_property(property_id: uuid.UUID) -> str:
    return f"properties:detail:{property_id}"


def feed_ads_by_city(city_id: uuid.UUID) -> str:
    return f"feed:ads:{city_id}"


def feed_ads_global() -> str:
    return "feed:ads:global"


def feed_page(cursor_str: str | None, preferences: Any = None, filters: Any = None) -> str:
    payload = {
        "cursor": cursor_str,
        "preferences": preferences,
        "filters": filters,
    }
    return f"feed:page:{_short_hash(payload)}"


def map_h3_cell(h3_index: str) -> str:
    return f"map:h3:{h3_index}"


def property_image_ids(property_id) -> str:
    return f"properties:images:{property_id}:ids"
