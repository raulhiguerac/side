from fastapi.concurrency import run_in_threadpool

from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.integrations.identity_provider.keycloak.auth_client import KeycloakAuthClient

from app.schemas.auth import AuthTokens
from app.core.exceptions.identity_provider import IdentityProviderUnavailableError


class KeycloakAuthenticationProvider(AuthenticationProvider):
    """
    Adapter de dominio para autenticación (login) usando Keycloak.
    Normaliza la respuesta del IDP a nuestro contrato interno.
    """

    def __init__(self, client: KeycloakAuthClient):
        self.client = client

    async def login(self, *, email: str, password: str) -> AuthTokens:
        token = await run_in_threadpool(
            self.client.keycloak_login,
            email,
            password,
        )

        access_token = token.get("access_token")
        expires_in = token.get("expires_in")

        if not access_token or expires_in is None:
            raise IdentityProviderUnavailableError(
                detail="Identity provider returned an invalid token response",
                context={
                    "missing_access_token": access_token is None,
                    "missing_expires_in": expires_in is None,
                },
            )

        return AuthTokens(
            access_token=access_token,
            expires_in=int(expires_in),
            refresh_token=token.get("refresh_token"),
            refresh_expires_in=token.get("refresh_expires_in"),
            token_type=token.get("token_type", "Bearer"),
        )
