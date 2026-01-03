import os
import uuid
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakGetError

from app.core.exceptions.integrations import(
    KeycloakRegisterError,
    KeycloakSetPasswordError,
    KeycloakDeleteAccountError
)

load_dotenv()

class KeycloakIntegration:
    def __init__(self):
        self.admin = KeycloakAdmin(
            server_url = os.getenv('KEYCLOAK_URL'),
            client_id = os.getenv('KC_CLIENT_ID'),
            realm_name = os.getenv('KC_REALM'),
            client_secret_key = os.getenv('KC_ADMIN_SECRET'),
            verify = True
        )
    
    def create_account_record(
            self, 
            email: str
        ) -> uuid.UUID:
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
            raise KeycloakRegisterError(detail=str(e), email=email, cause=e) from e

    def set_password(self, user_id: uuid.UUID, password: str) -> bool:
        """
        Establece la contraseña de forma permanente. 
        Retorna True si la operación fue exitosa.
        """
        try:
            self.admin.set_user_password(
                user_id=str(user_id), 
                password=password, 
                temporary=False
            )
            return True
        except Exception as e:
            raise KeycloakSetPasswordError(detail=str(e), user_id=str(user_id), cause=e) from e

    def delete_account(self, user_id: uuid.UUID) -> bool:
        """
        Elimina un usuario (útil para rollback).
        """
        try:
            self.admin.delete_user(user_id=str(user_id))
            return True
        except KeycloakGetError as e:
            status = getattr(e, "response_code", None) or getattr(e, "response_status", None)
            if status == 404:
                return True
            raise KeycloakDeleteAccountError(detail=str(e), user_id=str(user_id), cause=e) from e
        except Exception as e:
            raise KeycloakDeleteAccountError(detail=str(e), user_id=str(user_id), cause=e) from e