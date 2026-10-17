import uuid

from pydantic import EmailStr, Field

from app.schemas.base import StrictBase


class Principal(StrictBase):
    sub: uuid.UUID
    email: EmailStr | None = None
    email_verified: bool = False
    roles: list[str] = Field(default_factory=list)
