from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_ANALYTICS_URL: str = ""
    REDIS_URL: str = ""

    KC_JWKS_URL: str = ""
    KC_ISSUER: str = ""
    OIDC_AUDIENCE: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
