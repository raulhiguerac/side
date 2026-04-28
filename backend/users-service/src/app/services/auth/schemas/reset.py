from pydantic import EmailStr

from app.schemas.base import StrictBase


class RequestResetPasswordIn(StrictBase):
    email: EmailStr