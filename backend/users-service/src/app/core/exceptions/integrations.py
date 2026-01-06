from app.core.exceptions.base import BaseError

class IdentityProviderUnavailableError(BaseError):
    def __init__(self, detail: str | None = None, *, cause: Exception | None = None):
        super().__init__(
            message="Identity provider unavailable",
            code="IDENTITY_PROVIDER_UNAVAILABLE",
            status_code=502,
            context={"detail": detail},
            cause=cause,
        )

class KeycloakRegisterError(BaseError):
    def __init__(self, detail: str | None = None, *, email: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="Failed to register user in Keycloak",
            code="IDENTITY_PROVIDER_REGISTRATION_FAILED",
            status_code=502,
            context={"detail": detail, "email": email},
            cause=cause,
        )

class KeycloakSetPasswordError(BaseError):
    def __init__(self, detail: str | None = None, *, user_id: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="Failed to set password in keycloak",
            code="IDENTITY_PROVIDER_SET_PASSWORD_FAILED",
            status_code=502,
            context={"detail": detail, "user_id": user_id},
            cause=cause,
        )

class KeycloakDeleteAccountError(BaseError):
    def __init__(self, detail: str | None = None, *, user_id: str | None = None, cause: Exception | None = None):
        super().__init__(
            message="Failed to delete user in keycloak",
            code="IDENTITY_PROVIDER_DELETE_USER_FAILED",
            status_code=502,
            context={"detail": detail, "user_id": user_id},
            cause=cause,
        )