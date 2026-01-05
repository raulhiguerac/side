import uuid
from typing import Annotated, Union, Literal
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