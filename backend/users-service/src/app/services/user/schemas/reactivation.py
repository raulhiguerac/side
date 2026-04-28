from pydantic import EmailStr

from app.schemas.base import StrictBase


class RequestReactivationIn(StrictBase):
    email: EmailStr