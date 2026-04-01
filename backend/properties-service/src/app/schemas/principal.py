import uuid
from typing import Optional

from pydantic import EmailStr

from app.schemas.base import StrictBase


class Principal(StrictBase):
    sub: uuid.UUID
    email: Optional[EmailStr] = None
    email_verified: bool = False
    roles: list[str] = []
