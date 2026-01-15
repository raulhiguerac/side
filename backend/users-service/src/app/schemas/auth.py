import uuid
from typing import Annotated, Union, Literal, List, Optional
from pydantic import ConfigDict, EmailStr, Field

from app.schemas.base import StrictBase

class PersonRegisterIn(StrictBase):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    account_type: Literal["person"] = "person"

class OrganizationRegisterIn(StrictBase):
    display_name: str
    email: EmailStr
    password: str
    phone: str | None = None
    account_type: Literal["organization"] = "organization"

RegisterRequest = Annotated[
    Union[PersonRegisterIn, OrganizationRegisterIn],
    Field(discriminator="account_type")
]

class RegisterResponse(StrictBase):
    model_config = ConfigDict(from_attributes=True)
    account_id: uuid.UUID
    email: EmailStr

class AccountLogin(StrictBase):
    email: EmailStr
    password: str

class AuthTokens(StrictBase):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    refresh_expires_in: Optional[int] = None
    token_type: str = "Bearer"

class Principal(StrictBase):
    sub: str
    email: Optional[EmailStr]
    email_verified: bool = False
    scope: List[str] = []

class RefreshToken(StrictBase):
    refresh_token: str

class ChangePassword(StrictBase):
    old_password: str
    new_password: str