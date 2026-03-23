from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps.auth import get_current_principal
from app.api.deps.onboarding_use_cases import (
    get_complete_onboarding_cinterest_city_uc,
    get_complete_onboarding_intent_uc,
    get_complete_onboarding_interest_neighborhood_uc,
    get_complete_onboarding_interest_property_uc,
)
from app.schemas.common import Principal
from app.services.user.schemas.onboarding import (
    OnboardingCityRequest,
    OnboardingIntent,
    OnboardingNeighborhoodRequest,
    OnboardingPropertyTypeRequest,
)
from app.services.user.use_cases.onboarding.complete_intent import (
    CompleteOnboardingIntentUseCase,
)
from app.services.user.use_cases.onboarding.complete_interest_city import (
    CompleteCityIntentUseCase,
)
from app.services.user.use_cases.onboarding.complete_interest_neighborhood import (
    CompleteNeighborhoodInterestUseCase,
)
from app.services.user.use_cases.onboarding.complete_interest_property_type import (
    CompletePropertyTypeInterestUseCase,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/intent", status_code=status.HTTP_201_CREATED)
async def select_onboarding_intent(
    req: OnboardingIntent,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[CompleteOnboardingIntentUseCase, Depends(get_complete_onboarding_intent_uc)],
) -> None:
    await uc.execute(account_id=principal.sub, req=req)


@router.post("/city", status_code=status.HTTP_201_CREATED)
async def select_onboarding_city(
    req: OnboardingCityRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[CompleteCityIntentUseCase, Depends(get_complete_onboarding_cinterest_city_uc)],
) -> None:
    await uc.execute(account_id=principal.sub, locality_ids=req.locality_ids)


@router.post("/neighborhood", status_code=status.HTTP_201_CREATED)
async def select_onboarding_neighborhood(
    req: OnboardingNeighborhoodRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[CompleteNeighborhoodInterestUseCase, Depends(get_complete_onboarding_interest_neighborhood_uc)],
) -> None:
    await uc.execute(
        account_id=principal.sub,
        localities=[item.model_dump() for item in req.localities],
    )


@router.post("/property-type", status_code=status.HTTP_201_CREATED)
async def select_onboarding_property_type(
    req: OnboardingPropertyTypeRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    uc: Annotated[CompletePropertyTypeInterestUseCase, Depends(get_complete_onboarding_interest_property_uc)],
) -> None:
    await uc.execute(
        account_id=principal.sub,
        locality_id=req.locality_id,
        property_type=req.property_type,
    )