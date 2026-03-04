import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_CATALOG_URL", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Auth
    KC_JWKS_URL: str = os.getenv("KC_JWKS_URL", "")
    KC_ISSUER: str = os.getenv("KC_ISSUER", "")
    OIDC_AUDIENCE: str = os.getenv("OIDC_AUDIENCE", "")
    ADMIN_ROLE: str = os.getenv("ADMIN_ROLE", "admin")

    # Cache TTLs
    CACHE_TTL_CATALOG_SECONDS: int = 86400       # 1 day  — listas y entidades read-only
    CACHE_TTL_ENTITY_SECONDS: int = 2592000      # 30 days — entidades admin + geocode
    POI_STALE_THRESHOLD_DAYS: int = 30
    POI_LOCK_TTL_SECONDS: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
