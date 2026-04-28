import uuid

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.identity_provider import KeycloakDeleteAccountError
from app.integrations.identity_provider.keycloak.admin_client import KeycloakAdminClient
from app.services.auth.ports.identity_provider import IdentityProvider


class KeycloakIdentityProvider(IdentityProvider):

    def __init__(self, client: KeycloakAdminClient):
        self.client = client

    async def create_account(self, *, email: str, password: str) -> uuid.UUID:
        account_id = await run_in_threadpool(
            self.client.create_account_record,
            email
        )

        try:
            await run_in_threadpool(
                self.client.set_password,
                account_id,
                password,
            )
            return account_id

        except Exception as e:
            try:
                await run_in_threadpool(self.client.delete_account, account_id)
            except Exception as delete_exc:
                raise KeycloakDeleteAccountError(
                    detail="Failed to rollback Keycloak user after password error",
                    account_id=str(account_id),
                    cause=delete_exc,
                ) from e

            raise

    async def delete_user(self, account_id: uuid.UUID) -> None:
        await run_in_threadpool(self.client.delete_account, account_id)

    async def reset_password(self, *, account_id: uuid.UUID, new_password: str) -> None:
        return await run_in_threadpool(self.client.set_password, account_id, new_password)