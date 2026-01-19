from app.core.logging.logger import get_logger

from app.services.auth.ports.authentication_provider import AuthenticationProvider

logger = get_logger(__name__)


class LogoutUseCase:
    def __init__(
        self,
        *,
        auth_provider: AuthenticationProvider,
    ):
        self.auth_provider = auth_provider

    async def logout(self, *, refresh_token: str | None) -> None:

        """Invalidate the current session by revoking the refresh token."""

        if refresh_token:
            await self.auth_provider.logout(refresh_token=refresh_token)
        
        logger.info(
            "auth_logout_success",
            extra={
                "extra": {
                    "has_refresh_token": bool(refresh_token),
                }
            },
        )
