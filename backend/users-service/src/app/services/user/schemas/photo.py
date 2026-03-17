from app.schemas.base import StrictBase


class PhotoUploadOut(StrictBase):
    photo_url: str