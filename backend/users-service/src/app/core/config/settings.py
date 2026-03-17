import os


class Settings:
    FRONT_BASE_URL: str
    CACHE_REACTIVATION_TTL_SECONDS: int

    def __init__(self) -> None:
        self.FRONT_BASE_URL = os.getenv("FRONT_BASE_URL")
        if not self.FRONT_BASE_URL:
            raise RuntimeError("FRONT_BASE_URL is not set")

        self.CACHE_REACTIVATION_TTL_SECONDS = int(
            os.getenv("CACHE_REACTIVATION_TTL_SECONDS", "900")
        )


settings = Settings()