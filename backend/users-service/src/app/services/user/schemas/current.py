import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import EmailStr, Field

from app.models.account import AccountIntent, OnboardingStep
from app.schemas.base import StrictBase


class CurrentUserPerson(StrictBase):
    first_name: str
    last_name: str
    phone: str | None
    photo_url: str | None
    description: str | None
    intent: AccountIntent | None
    account_type: Literal['person']
    created_at: datetime | None = None

class CurrentUserOrganization(StrictBase):
    display_name: str
    phone: str | None
    photo_url: str | None
    description: str | None
    intent: AccountIntent | None
    account_type: Literal["organization"]
    created_at: datetime | None = None

class CurrentUserProfileOut(StrictBase):
    profile: Annotated[
        CurrentUserPerson | CurrentUserOrganization,
        Field(discriminator="account_type")
    ]

class CurrentUserOut(StrictBase):
    account_id: uuid.UUID
    email: EmailStr
    account_type: Literal["person", "organization"]
    onboarding_step: OnboardingStep
    is_active: bool
    is_admin: bool = False


class UserInterestsResponse(StrictBase):
    localities: list[uuid.UUID]
    neighborhoods: dict[str, list[uuid.UUID]]
    properties: dict[str, list[str]]