import uuid


def client_properties(user_id: uuid.UUID) -> str:
    return f"properties:user:{user_id}"


def cache_property(property_id: uuid.UUID) -> str:
    return f"properties:detail:{property_id}"
