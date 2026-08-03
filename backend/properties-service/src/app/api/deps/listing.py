from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.integrations.cache.redis.cache import CacheClient
from app.integrations.catalog.catalog_client import CatalogClient
from app.integrations.storage.minio.storage import StorageClient
from app.integrations.users.users_client import UsersClient
from app.services.listing.adapters.sql_unit_of_work import SqlListingUnitOfWork
from app.services.listing.ports.unit_of_work import ListingUnitOfWork
from app.services.listing.use_cases.images.confirm_image_uploads import ConfirmImageUploadsUseCase
from app.services.listing.use_cases.images.delete_property_images import DeletePropertyImagesUseCase
from app.services.listing.use_cases.images.request_presigned_urls import RequestPresignedUrlsUseCase
from app.services.listing.use_cases.property_core.create_property import CreatePropertyUseCase
from app.services.listing.use_cases.property_core.delete_property import DeletePropertyUseCase
from app.services.listing.use_cases.property_core.get_my_properties import GetMyPropertiesUseCase
from app.services.listing.use_cases.property_core.get_property import GetPropertyUseCase
from app.services.listing.use_cases.property_core.get_public_user_properties import GetPublicUserPropertiesUseCase
from app.services.listing.use_cases.property_core.set_property_visibility import SetPropertyVisibilityUseCase
from app.services.listing.use_cases.property_core.update_property import UpdatePropertyUseCase
from app.services.shared.adapters.catalog_adapter import CatalogAdapter
from app.services.shared.adapters.minio_storage_adapter import MinioStorageAdapter
from app.services.shared.adapters.redis_cache_adapter import RedisCacheAdapter
from app.services.shared.adapters.users_adapter import UsersAdapter
from app.services.shared.ports.cache import CachePort
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.ports.storage import StoragePort
from app.services.shared.ports.users_gateway import UsersGateway


# -------------------------------------------------------------------------
# Stateless providers (safe to cache at module level)
# -------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_cache_port() -> CachePort:
    return RedisCacheAdapter(CacheClient())


@lru_cache(maxsize=1)
def get_catalog_gateway() -> CatalogGateway:
    return CatalogAdapter(CatalogClient())


@lru_cache(maxsize=1)
def get_users_gateway() -> UsersGateway:
    return UsersAdapter(UsersClient())


@lru_cache(maxsize=1)
def get_storage_port() -> StoragePort:
    return MinioStorageAdapter(StorageClient())


# -------------------------------------------------------------------------
# Unit of Work (request-scoped)
# -------------------------------------------------------------------------

def get_listing_uow(session: Session = Depends(get_session)) -> ListingUnitOfWork:
    return SqlListingUnitOfWork(session=session)


# -------------------------------------------------------------------------
# Use cases
# -------------------------------------------------------------------------

def get_property_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetPropertyUseCase:
    return GetPropertyUseCase(uow=uow, cache=cache)


def get_my_properties_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetMyPropertiesUseCase:
    return GetMyPropertiesUseCase(uow=uow, cache=cache)


def get_public_user_properties_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> GetPublicUserPropertiesUseCase:
    return GetPublicUserPropertiesUseCase(uow=uow, cache=cache)


def get_create_property_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    catalog: CatalogGateway = Depends(get_catalog_gateway),
) -> CreatePropertyUseCase:
    return CreatePropertyUseCase(uow=uow, catalog=catalog)


def get_update_property_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> UpdatePropertyUseCase:
    return UpdatePropertyUseCase(
        uow = uow,
        cache_client = cache,
    )


def get_delete_property_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> DeletePropertyUseCase:
    return DeletePropertyUseCase(uow=uow, cache=cache)


def get_set_visibility_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> SetPropertyVisibilityUseCase:
    return SetPropertyVisibilityUseCase(uow=uow, cache=cache)


def get_request_presigned_urls_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    storage: StoragePort = Depends(get_storage_port),
    cache: CachePort = Depends(get_cache_port),
) -> RequestPresignedUrlsUseCase:
    return RequestPresignedUrlsUseCase(uow=uow, storage=storage, cache=cache)


def get_confirm_image_uploads_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> ConfirmImageUploadsUseCase:
    return ConfirmImageUploadsUseCase(uow=uow, cache_client=cache)


def get_delete_property_images_uc(
    uow: ListingUnitOfWork = Depends(get_listing_uow),
    cache: CachePort = Depends(get_cache_port),
) -> DeletePropertyImagesUseCase:
    return DeletePropertyImagesUseCase(uow=uow, cache_client=cache)
