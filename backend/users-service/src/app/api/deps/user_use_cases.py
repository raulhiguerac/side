import os
from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session

from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.storage import StoragePort
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.shared.ports.email_sender import EmailSenderPort

from app.services.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from app.services.shared.adapters.minio_storage_adapter import MinioStorageAdapter
from app.services.user.adapters.sql_unit_of_work import SqlUserUnitOfWork
from app.services.shared.adapters.brevo_email_sender_adapter import BrevoSenderAdapter

from app.integrations.cache.redis.cache import CacheClient
from app.integrations.storage.minio.storage import StorageClient
from app.integrations.email.brevo.client import EmailClient

from app.services.user.helpers.current_account_reader import CurrentAccountReader
from app.services.user.helpers.current_profile_reader import CurrentProfileReader

from app.services.user.services.get_profile_orchestrator import ProfileApplicationService
from app.services.user.services.reactivation_mailer import ReactivationMailer

from app.services.user.use_cases.account.get_current_account import GetCurrentAccountUseCase
from app.services.user.use_cases.account.deactivate_current_account import DeactivateCurrentAccountUseCase
from app.services.user.use_cases.account.request_account_reactivation import RequestReactivationUseCase
from app.services.user.use_cases.account.reactivate_current_account import ConfirmReactivationUseCase

from app.services.user.use_cases.profile.get_current_profile import GetCurrentProfileUseCase
from app.services.user.use_cases.profile.update_current_profile import UpdateCurrentProfileUseCase
from app.services.user.use_cases.profile.upload_profile_photo import UpdateCurrentProfilePhotoUseCase

from app.core.exceptions.storage import StorageMisconfiguredError

# -------------------------------------------------------------------------
# Providers (stateless → safe to cache)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())

@lru_cache(maxsize=1)
def get_storage_port() -> StoragePort:
    return MinioStorageAdapter(StorageClient())

@lru_cache(maxsize=1)
def get_profile_photos_bucket() -> str:
    bucket = os.getenv("PROFILE_PHOTOS_BUCKET")
    if not bucket:
        raise StorageMisconfiguredError(
            context={"missing": "PROFILE_PHOTOS_BUCKET"}
        )
    return bucket

@lru_cache(maxsize=1)
def get_public_base_url() -> str:
    base_url = os.getenv("STORAGE_PUBLIC_BASE_URL")
    if not base_url:
        raise StorageMisconfiguredError(
            context={"missing": "STORAGE_PUBLIC_BASE_URL"}
        )
    return base_url

@lru_cache(maxsize=1)
def get_email_sender() -> EmailSenderPort:
    return BrevoSenderAdapter(EmailClient())


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

def get_profile_application(
    profile_reader: CurrentProfileReader = Depends(get_current_profile_reader),
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
) -> ProfileApplicationService:
    return ProfileApplicationService(
        profile_reader=profile_reader,
        account_reader=account_reader
    )

def get_reactivation_mailer(
    email_sender: EmailSenderPort = Depends(get_email_sender)
) -> ReactivationMailer:
    return ReactivationMailer(email_sender=email_sender)
    

# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_current_account_uc(
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
) -> GetCurrentAccountUseCase:
    return GetCurrentAccountUseCase(account_reader=account_reader)

def get_current_profile_uc(
    profile_service: ProfileApplicationService = Depends(get_profile_application),
) -> GetCurrentProfileUseCase:
    return GetCurrentProfileUseCase(
        profile_service=profile_service,
    )

def get_update_current_profile_photo_uc(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    storage: StoragePort = Depends(get_storage_port),
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
    profile_reader: CurrentProfileReader = Depends(get_current_profile_reader),
    bucket_name: str = Depends(get_profile_photos_bucket),
    base_url: str = Depends(get_public_base_url)

) -> UpdateCurrentProfilePhotoUseCase:
    return UpdateCurrentProfilePhotoUseCase(
        uow=uow,
        cache_client=cache,
        storage_client=storage,
        account_reader=account_reader,
        profile_reader=profile_reader,
        bucket_name=bucket_name,
        base_url=base_url,
    )

def get_update_current_profile_uc(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    account_reader: CurrentAccountReader = Depends(get_current_account_reader),
    profile_reader: CurrentProfileReader = Depends(get_current_profile_reader),

) -> UpdateCurrentProfileUseCase:
    return UpdateCurrentProfileUseCase(
        uow=uow,
        cache_client=cache,
        account_reader=account_reader,
        profile_reader=profile_reader,
    )

def get_deactivate_current_account_uc(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
) -> DeactivateCurrentAccountUseCase:
    return DeactivateCurrentAccountUseCase(
        uow=uow,
        cache_client=cache,
    )

def get_request_reactivation_uc(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port),
    profile_service: ProfileApplicationService = Depends(get_profile_application),
    reactivation_mailer: ReactivationMailer = Depends(get_reactivation_mailer),
) -> RequestReactivationUseCase:
    return RequestReactivationUseCase(
        uow=uow,
        cache_client=cache,
        profile_service=profile_service,
        reactivation_mailer=reactivation_mailer
    )

def get_confirm_reactivation_uc(
    uow: UserUnitOfWork = Depends(get_uow),
    cache: CachePort = Depends(get_cache_port)
) -> ConfirmReactivationUseCase:
    return ConfirmReactivationUseCase(
        uow=uow,
        cache_client=cache,
    )