from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session

from app.services.user.ports.cache import CachePort
from app.services.user.ports.unit_of_work import UserUnitOfWork

from app.services.user.adapters.redis_cache_adapter import RedisCacheAdapter
from app.services.user.adapters.sql_unit_of_work import SqlUserUnitOfWork

from app.integrations.cache.redis.cache import CacheClient

from app.services.user.helpers.current_account_reader import CurrentAccountReader
from app.services.user.helpers.current_profile_reader import CurrentProfileReader

from app.services.user.use_cases.get_current_account import GetCurrentAccountUseCase
from app.services.user.use_cases.get_current_profile import GetCurrentProfileUseCase


# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_uow(session: Session = Depends(get_session)) -> UserUnitOfWork:
    return SqlUserUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Readers / Resolvers (request-scoped if they depend on UoW)
# -------------------------------------------------------------------------

def get_current_account_reader(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CurrentAccountReader:
    return CurrentAccountReader(uow=uow, cache_client=cache)

def get_current_profile_reader(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> CurrentProfileReader:
    return CurrentProfileReader(uow=uow, cache_client=cache)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_current_account_uc(
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
) -> GetCurrentAccountUseCase:
    return GetCurrentAccountUseCase(account_reader=account_reader)

def get_current_profile_uc(
    profile_reader: CurrentProfileReader = Depends(get_current_profile_reader),
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
) -> GetCurrentProfileUseCase:
    return GetCurrentProfileUseCase(
        profile_reader=profile_reader,
        account_reader=account_reader
    )
