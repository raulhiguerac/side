import os
import uuid
from typing import Dict, Any
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError

from app.core.exceptions.identity_provider import(
    KeycloakRegisterError,
    KeycloakSetPasswordError,
    KeycloakDeleteAccountError,
    IdentityProviderUnavailableError,
    IdentityProviderMisconfiguredError
)

from app.integrations._utils import get_keycloak_status

class KeycloakAdminClient:
    def __init__(self):
        server_url = os.getenv('KEYCLOAK_URL')
        client_id = os.getenv('KC_CLIENT_ID')
        realm_name = os.getenv('KC_REALM')
        client_secret_key = os.getenv('KC_ADMIN_SECRET')

        missing = [
            name for name, value in {
                "KEYCLOAK_URL": server_url,
                "KC_CLIENT_ID": client_id,
                "KC_REALM": realm_name,
                "KC_ADMIN_SECRET": client_secret_key,
            }.items()
            if not value
        ]

        if missing:
            raise IdentityProviderMisconfiguredError(
                detail=f"Missing Keycloak env vars: {', '.join(missing)}"
            )
        
        self.admin = KeycloakAdmin(
            server_url = server_url,
            client_id = client_id,
            realm_name = realm_name,
            client_secret_key = client_secret_key,
            verify = True
        )
    
    def create_account_record(self, email: str) -> uuid.UUID:
        """
        Crea un usuario en Keycloak y extrae el UUID generado.
        """
        try:
            user_data: Dict[str, Any] = {
                "email": email,
                "username": email,
                "enabled": True
            }
            
            user_id_str: str = self.admin.create_user(user_data)
            
            return uuid.UUID(user_id_str)
        
        except Exception as e:
            status = get_keycloak_status(e)

            if status is None or status >= 500:
                raise IdentityProviderUnavailableError(cause=e) from e

            raise KeycloakRegisterError(
                detail=str(e),
                email=email,
                cause=e
            ) from e

    def set_password(self, user_id: uuid.UUID, password: str) -> None:
        """
        Establece la contraseña de forma permanente. 
        Retorna True si la operación fue exitosa.
        """
        try:
            self.admin.set_user_password(
                user_id=str(user_id),
                password=password,
                temporary=False,
            )
        except Exception as e:
            status = get_keycloak_status(e)
            if status is None or status >= 500:
                raise IdentityProviderUnavailableError(cause=e) from e

            raise KeycloakSetPasswordError(
                detail=str(e),
                user_id=str(user_id),
                cause=e,
            ) from e

    def delete_account(self, user_id: uuid.UUID) -> None:
        """
        Elimina un usuario (útil para rollback).
        """
        try:
            self.admin.delete_user(user_id=str(user_id))

        except KeycloakGetError as e:
            status = get_keycloak_status(e)
            if status == 404:
                return
            if status is None or status >= 500:
                raise IdentityProviderUnavailableError(cause=e) from e

            raise KeycloakDeleteAccountError(
                detail=str(e),
                user_id=str(user_id),
                cause=e,
            ) from e

        except Exception as e:
            raise IdentityProviderUnavailableError(cause=e) from e