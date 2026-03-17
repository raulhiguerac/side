import uuid

from app.models.account import OnboardingStep
from app.schemas.base import StrictBase


class OnboardingIntent(StrictBase):
    intent: OnboardingStep


class OnboardingCityRequest(StrictBase):
    locality_id: uuid.UUID


class OnboardingNeighborhoodRequest(StrictBase):
    locality_id: uuid.UUID
    neighborhoods: dict[int, uuid.UUID]


class OnboardingPropertyTypeRequest(StrictBase):
    locality_id: uuid.UUID
    property_type: list[str]