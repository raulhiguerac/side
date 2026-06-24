import uuid
from datetime import datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import EmailStr, Field

from app.models.account import AccountIntent, OnboardingStep
from app.schemas.base import StrictBase


class CurrentUserPerson(StrictBase):
    first_name: str
    last_name: str
    phone: Optional[str]
    photo_url: Optional[str]
    description: Optional[str]
    intent: Optional[AccountIntent]
    account_type: Literal['person']
    created_at: Optional[datetime] = None

class CurrentUserOrganization(StrictBase):
    display_name: str
    phone: Optional[str]
    photo_url: Optional[str]
    description: Optional[str]
    intent: Optional[AccountIntent]
    account_type: Literal["organization"]
    created_at: Optional[datetime] = None

class CurrentUserProfileOut(StrictBase):
    profile: Annotated[
        Union[CurrentUserPerson,CurrentUserOrganization],
        Field(discriminator="account_type")
    ]

class CurrentUserOut(StrictBase):
    account_id: uuid.UUID
    email: EmailStr
    account_type: Literal["person", "organization"]
    onboarding_step: OnboardingStep
    is_active: bool


class UserInterestsResponse(StrictBase):
    localities: list[uuid.UUID]
    neighborhoods: dict[str, list[uuid.UUID]]
    properties: dict[str, list[str]]