from app.schemas.base import StrictBase

class ChangePassword(StrictBase):
    old_password: str
    new_password: str