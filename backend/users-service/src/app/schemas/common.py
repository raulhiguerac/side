import uuid
from typing import List, Optional

from pydantic import EmailStr

from app.schemas.base import StrictBase


class Principal(StrictBase):
    sub: uuid.UUID
    email: Optional[EmailStr]
    email_verified: bool = False
    scope: List[str] = []
    roles: List[str] = []