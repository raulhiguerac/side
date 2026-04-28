from pydantic import EmailStr

from app.schemas.base import StrictBase


class AccountLogin(StrictBase):
    email: EmailStr
    password: str