import uuid

from app.models.account import OnboardingStep
from app.schemas.base import StrictBase


class OnboardingIntent(StrictBase):
    intent: OnboardingStep


class OnboardingCityRequest(StrictBase):
    locality_ids: list[uuid.UUID]


class OnboardingNeighborhoodItem(StrictBase):
    locality_id: uuid.UUID
    neighborhoods: dict[int, uuid.UUID]


class OnboardingNeighborhoodRequest(StrictBase):
    localities: list[OnboardingNeighborhoodItem]


class OnboardingPropertyTypeRequest(StrictBase):
    locality_id: uuid.UUID
    property_type: list[str]