import uuid


def client_properties(user_id: uuid.UUID) -> str:
    return f"properties:user:{user_id}"


def cache_property(property_id: uuid.UUID) -> str:
    return f"properties:detail:{property_id}"


def feed_ads_by_city(city_id: uuid.UUID) -> str:
    return f"feed:ads:{city_id}"


def feed_ads_global() -> str:
    return "feed:ads:global"


def map_h3_cell(h3_index: str) -> str:
    return f"map:h3:{h3_index}"


def property_image_ids(property_id) -> str:
    return f"properties:images:{property_id}:ids"
