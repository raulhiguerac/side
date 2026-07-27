from typing import Protocol

from app.services.shared.schemas.users_schemas import ResolvedAccount


class UsersGateway(Protocol):
    async def resolve_accounts(self, *, emails: list[str]) -> list[ResolvedAccount]: ...
