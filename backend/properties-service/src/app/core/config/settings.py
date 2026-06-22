import os
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
    PUBLIC_PROPERTIES_PAGE_SIZE: int = 20

    # Storage
    BUCKET_PHOTOS_PROPERTIES: str = ""
    STORAGE_PUBLIC_BASE_URL: str = ""
    PRESIGNED_URL_TTL_SECONDS: int = 300  # 5 min
    IMAGE_UPLOAD_BATCH_TTL_SECONDS: int = 300  # 5 min
    PROPERTY_IMAGE_IDS_CACHE_TTL_SECONDS: int = 300  # 5 min
    MAX_IMAGES_PER_PROPERTY: int = 20

    class Config:
        env_file = ".env"


settings = Settings()
