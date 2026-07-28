from app.core.exceptions.listing import UsersServiceUnavailableError
from app.integrations.users.users_client import UsersClient
from app.services.shared.ports.users_gateway import UsersGateway
from app.services.shared.schemas.users_schemas import ResolvedAccount


class UsersAdapter(UsersGateway):
    def __init__(self, client: UsersClient) -> None:
        self._client = client

    async def resolve_accounts(self, *, emails: list[str]) -> list[ResolvedAccount]:
        try:
            raw = await self._client.resolve_by_emails(emails=emails)
            return [ResolvedAccount(account_id=item[0], email=item[1]) for item in raw]
        except Exception as e:
            raise UsersServiceUnavailableError(cause=e) from e
