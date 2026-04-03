import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # Cache TTLs (seconds)
    CACHE_TTL_USER_PROPERTIES_SECONDS: int = 1800  # 30 min
    CACHE_TTL_PROPERTY_SECONDS: int = 21600  # 6 hours

    class Config:
        env_file = ".env"


settings = Settings()
