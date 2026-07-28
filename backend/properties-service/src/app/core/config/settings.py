import os
import uuid

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_PROPERTIES_URL: str = os.getenv("DATABASE_PROPERTIES_URL", "")

    # Catalog service
    CATALOG_URL: str = os.getenv("CATALOG_URL", "http://localhost:8001")

    # Auth (Keycloak)
    KC_JWKS_URL: str = os.getenv("KC_JWKS_URL", "")
    KC_ISSUER: str = os.getenv("KC_ISSUER", "")
    OIDC_AUDIENCE: str = os.getenv("OIDC_AUDIENCE", "")
    ADMIN_ROLE: str = os.getenv("ADMIN_ROLE", "admin")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Cache TTLs (seconds)
    CACHE_TTL_USER_PROPERTIES_SECONDS: int = 1800  # 30 min
    CACHE_TTL_PROPERTY_SECONDS: int = 21600  # 6 hours

    # Feed
    FEED_PAGE_SIZE: int = 20
    FEED_MAX_RESULTS: int = 300
    FEED_AD_INTERVAL: int = 5  # 1 ad every N organic results
    FEED_PAGE_CACHE_TTL_SECONDS: int = 300  # 5 min

    # Public user properties (storefront del publicante)
    # 21 = page_size 20 + 1 extra para detectar has_more sin COUNT(*)
    PUBLIC_PROPERTIES_PAGE_SIZE: int = 21

    # Storage
    BUCKET_PHOTOS_PROPERTIES: str = ""
    BUCKET_BULK_PROPERTIES: str = ""

    # Bulk jobs
    # A job still pending past this is assumed dead (the process that ran the
    # background task died), so status reads report it as failed.
    BULK_JOB_TIMEOUT_SECONDS: int = 600  # 10 min

    # Namespace for deriving property ids from the CSV external_id, which is what
    # makes a re-import upsert instead of duplicating. Treat as frozen: changing
    # it re-keys every property, so previously imported rows would come back in
    # as new records.
    BULK_PROPERTY_ID_NAMESPACE: uuid.UUID = uuid.UUID("d1bbd361-a2e7-44b9-b6e3-2a9d699dcdb5")
    STORAGE_PUBLIC_BASE_URL: str = ""
    PRESIGNED_URL_TTL_SECONDS: int = 300  # 5 min
    IMAGE_UPLOAD_BATCH_TTL_SECONDS: int = 300  # 5 min
    PROPERTY_IMAGE_IDS_CACHE_TTL_SECONDS: int = 300  # 5 min
    MAX_IMAGES_PER_PROPERTY: int = 20
    STORAGE_CHUNK_SIZE_BYTES: int = 10_000_000  # 10 MB, usado por chunk_file

    class Config:
        env_file = ".env"


settings = Settings()
