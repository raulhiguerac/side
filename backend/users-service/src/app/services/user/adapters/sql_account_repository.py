import uuid

from app.core.exceptions.account import AccountNotFoundError
from app.services.shared.adapters.sql_account_reader import SqlAccountReader
from app.services.user.ports.account_repository import AccountRepository
from app.services.user.schemas.current import UserInterestsResponse


class UserAccountRepository(AccountRepository):
    def __init__(self, reader: SqlAccountReader):
        self._reader = reader

    async def get_by_id(self, *, account_id):
        account = await self._reader.get_by_id(account_id=account_id)
        if account is None:
            raise AccountNotFoundError(account_id=account_id)
        return account

    async def get_by_email(self, *, email):
        account = await self._reader.get_by_email(email=email)
        if account is None:
            raise AccountNotFoundError(email=email)
        return account

    async def get_interests(self, *, account_id: uuid.UUID) -> UserInterestsResponse:
        raw = await self._reader.get_interests_by_account(account_id=account_id)

        localities = raw["localities"]
        interest_map = {loc.id: str(loc.city_id) for loc in localities}

        neighborhoods: dict[str, list[uuid.UUID]] = {}
        for n in raw["neighborhoods"]:
            city_key = interest_map[n.user_interest_id]
            neighborhoods.setdefault(city_key, []).append(n.neighborhood_id)

        properties: dict[str, list[str]] = {}
        for p in raw["properties"]:
            city_key = interest_map[p.user_interest_id]
            properties.setdefault(city_key, []).append(p.property_type.value)

        return UserInterestsResponse(
            localities=[loc.city_id for loc in localities],
            neighborhoods=neighborhoods,
            properties=properties,
        )
