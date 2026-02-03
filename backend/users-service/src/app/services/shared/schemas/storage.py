from app.schemas.base import StrictBase 

class UploadResult(StrictBase):
    bucket: str
    key: str