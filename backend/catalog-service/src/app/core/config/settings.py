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
    # Resolución H3 usada en todo el servicio para indexar y consultar POIs.
    # INVARIANTE: cambiar este valor invalida todos los `h3_index` ya escritos
    # en `points_of_interest` (quedan en la resolución vieja y las queries por
    # celda dejan de matchear → cero resultados sin error). Cambiarlo exige una
    # migración que recompute `h3_index` de toda la tabla. No es un toggle inocuo.
    H3_RESOLUTION: int = 9
    OVERPASS_TIMEOUT_SECONDS: int = 30
    ORS_URL: str = os.getenv("ORS_URL", "")
    ORS_TIMEOUT_SECONDS: float = 5.0

    class Config:
        env_file = ".env"


settings = Settings()
