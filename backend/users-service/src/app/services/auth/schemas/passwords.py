from app.schemas.base import StrictBase

class ChangePassword(StrictBase):
    old_password: str
    new_password: str

class ResetPassword(StrictBase):
    new_password: str
    confirm_password: str