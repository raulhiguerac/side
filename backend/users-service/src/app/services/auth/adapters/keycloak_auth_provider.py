from fastapi.concurrency import run_in_threadpool

from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.integrations.identity_provider.keycloak.auth_client import KeycloakAuthClient

from app.services.auth.schemas.tokens import AuthTokens
from app.core.exceptions.identity_provider import IdentityProviderUnavailableError


class KeycloakAuthenticationProvider(AuthenticationProvider):
    """
    Adapter de dominio para autenticación (login) usando Keycloak.
    Normaliza la respuesta del IDP a nuestro contrato interno.
    """

    def __init__(self, client: KeycloakAuthClient):
        self._client = client

    @staticmethod
    def _normalize_idp_tokens(*, token: dict) -> AuthTokens:
        access_token = token.get("access_token")
        expires_in = token.get("expires_in")

        if not access_token or expires_in is None:
            raise IdentityProviderUnavailableError(
                detail="Identity provider returned an invalid token response",
                context={
                    "missing_access_token": not bool(access_token),
                    "missing_expires_in": expires_in is None,
                },
            )
        
        try:
            expires_in = int(expires_in)
        except (TypeError, ValueError):
            raise IdentityProviderUnavailableError(
                detail="Identity provider returned a non-castable expires_in",
                context={
                    "expires_in": str(expires_in),
                },
            )

        return AuthTokens(
            access_token=access_token,
            expires_in=int(expires_in),
            refresh_token=token.get("refresh_token"),
            refresh_expires_in=token.get("refresh_expires_in"),
            token_type=token.get("token_type", "Bearer"),
        )

    async def login(self, *, email: str, password: str) -> AuthTokens:
        token = await run_in_threadpool(
            self._client.keycloak_login,
            email,
            password,
        )
        return self._normalize_idp_tokens(token=token)
    
    async def refresh_token(self, *, refresh_token: str) -> AuthTokens:
        token = await run_in_threadpool(
            self._client.keycloak_refresh_token,
            refresh_token
        )
        return self._normalize_idp_tokens(token=token)
    
    async def logout(self, *, refresh_token: str) -> None:
        await run_in_threadpool(self._client.keycloak_revoke_token, refresh_token)
