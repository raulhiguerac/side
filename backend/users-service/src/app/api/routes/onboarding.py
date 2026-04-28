from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps.auth import get_current_principal
from app.api.deps.onboarding_use_cases import (
    get_complete_onboarding_intent_uc,
)

from app.schemas.common import Principal
from app.services.user.schemas.onboarding import OnboardingIntent
from app.services.user.use_cases.onboarding.complete_intent import (
    CompleteOnboardingIntentUseCase,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post(
    "/intent",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def select_onboarding_intent(
    req: OnboardingIntent,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[
        CompleteOnboardingIntentUseCase,
        Depends(get_complete_onboarding_intent_uc),
    ],
) -> None:
    await uc.execute(
        account_id=principal.sub,
        req=req,
    )