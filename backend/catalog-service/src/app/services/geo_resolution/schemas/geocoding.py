from app.schemas.base import StrictBase

class GeocodingResult(StrictBase):
    latitude: float
    longitude: float
    formatted_address: str | None = None
