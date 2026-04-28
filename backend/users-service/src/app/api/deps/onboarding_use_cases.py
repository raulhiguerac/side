from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session

from app.integrations.cache.redis.cache import CacheClient
from app.services.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from app.services.shared.ports.cache import CachePort

from app.services.user.adapters.sql_unit_of_work import SqlUserUnitOfWork
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.use_cases.onboarding.complete_intent import (
    CompleteOnboardingIntentUseCase,
)


# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())


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