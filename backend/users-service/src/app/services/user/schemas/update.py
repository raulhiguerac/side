from typing import Annotated, Literal, Optional, Union

from pydantic import Field

from app.models.account import AccountIntent
from app.schemas.base import StrictBase


class UserPersonUpdate(StrictBase):
    phone: Optional[str] = None
    description: Optional[str] = None
    intent: Optional[AccountIntent] = None
    account_type: Literal["person"]

class UserOrganizationUpdate(StrictBase):
    phone: Optional[str] = None
    description: Optional[str] = None
    intent: Optional[AccountIntent] = None
    account_type: Literal["organization"]

UpdateRequest = Annotated[
    Union[UserPersonUpdate, UserOrganizationUpdate],
    Field(discriminator="account_type")
]