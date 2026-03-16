import uuid
from typing import Protocol

from app.models.account import OnboardingStep
from app.models.interests import UserNeighborhoodInterest

class OnboardingCompletionRepository(Protocol):

    def get_interest_by_account_locality(
        self,
        *,
        account_id: uuid.UUID,
        locality_id: uuid.UUID,
    ) -> uuid.UUID: ...

    def mark_completed(
        self,
        *,
        account_id: uuid.UUID,
        key: OnboardingStep,
    ) -> bool: ...

    def save_locality(
        self,
        *,
        account_id: uuid.UUID,
        locality_id: uuid.UUID,
    ) -> None: ...

    def save_neighborhoods(
        self,
        *,
        neighborhoods: list[UserNeighborhoodInterest]
    ) -> None: ...