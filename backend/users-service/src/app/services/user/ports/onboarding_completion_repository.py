import uuid
from typing import Protocol

from app.models.account import OnboardingStep

class OnboardingCompletionRepository(Protocol):
    async def mark_completed(
        self,
        *,
        account_id: uuid.UUID,
        key: OnboardingStep,
    ) -> bool: ...