import uuid
from typing import Protocol

from app.services.shared.schemas.users_schemas import ResolvedAccount


class UsersGateway(Protocol):
    async def resolve_accounts(self, *, account_ids: list[uuid.UUID]) -> list[ResolvedAccount]: ...
