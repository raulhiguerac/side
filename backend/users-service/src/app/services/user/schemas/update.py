from typing import Annotated, Literal

from pydantic import Field

from app.models.account import AccountIntent
from app.schemas.base import StrictBase


class UserPersonUpdate(StrictBase):
    phone: str | None = None
    description: str | None = None
    intent: AccountIntent | None = None
    account_type: Literal["person"]

class UserOrganizationUpdate(StrictBase):
    phone: str | None = None
    description: str | None = None
    intent: AccountIntent | None = None
    account_type: Literal["organization"]

UpdateRequest = Annotated[
    UserPersonUpdate | UserOrganizationUpdate,
    Field(discriminator="account_type")
]