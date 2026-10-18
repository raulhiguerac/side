from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.shared.cache import get_cache_port
from app.api.deps.shared.db import get_session
from app.services.shared.ports.cache import CachePort
from app.services.user.adapters.sql_unit_of_work import SqlUserUnitOfWork
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork
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

# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------


def get_uow(session: Annotated[Session, Depends(get_session)]) -> UserUnitOfWork:
    return SqlUserUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Readers / Resolvers (request-scoped if they depend on UoW)
# -------------------------------------------------------------------------


def get_current_profile_reader(
    uow: Annotated[UserUnitOfWork, Depends(get_uow)],
    cache: Annotated[CachePort, Depends(get_cache_port)],
) -> CurrentProfileReader:
    return CurrentProfileReader(uow=uow, cache_client=cache)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------


def get_complete_onboarding_intent_uc(
    uow: Annotated[UserUnitOfWork, Depends(get_uow)],
    cache: Annotated[CachePort, Depends(get_cache_port)],
    profile_reader: Annotated[CurrentProfileReader, Depends(get_current_profile_reader)],
) -> CompleteOnboardingIntentUseCase:
    return CompleteOnboardingIntentUseCase(
        uow=uow,
        cache=cache,
        profile_reader=profile_reader,
    )

def get_complete_onboarding_cinterest_city_uc(
    uow: Annotated[UserUnitOfWork, Depends(get_uow)],
    cache: Annotated[CachePort, Depends(get_cache_port)],
    profile_reader: Annotated[CurrentProfileReader, Depends(get_current_profile_reader)],
) -> CompleteCityIntentUseCase:
    return CompleteCityIntentUseCase(
        uow=uow,
        cache=cache,
        profile_reader=profile_reader,
    )

def get_complete_onboarding_interest_neighborhood_uc(
    uow: Annotated[UserUnitOfWork, Depends(get_uow)],
    cache: Annotated[CachePort, Depends(get_cache_port)],
    profile_reader: Annotated[CurrentProfileReader, Depends(get_current_profile_reader)],
) -> CompleteNeighborhoodInterestUseCase:
    return CompleteNeighborhoodInterestUseCase(
        uow=uow,
        cache=cache,
        profile_reader=profile_reader,
    )

def get_complete_onboarding_interest_property_uc(
    uow: Annotated[UserUnitOfWork, Depends(get_uow)],
    cache: Annotated[CachePort, Depends(get_cache_port)],
    profile_reader: Annotated[CurrentProfileReader, Depends(get_current_profile_reader)],
) -> CompletePropertyTypeInterestUseCase:
    return CompletePropertyTypeInterestUseCase(
        uow=uow,
        cache=cache,
        profile_reader=profile_reader,
    )