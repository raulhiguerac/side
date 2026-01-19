import uuid

from app.schemas.auth import Principal
from app.schemas.user import CurrentUserOut
from app.core.exceptions.auth import InvalidTokenException

from app.services.user.helpers.current_account_reader import CurrentAccountReader


class GetCurrentAccountUseCase:
    def __init__(self, *, account_reader: CurrentAccountReader) -> None:
        self.account_reader = account_reader

    async def execute(self, *, principal: Principal) -> CurrentUserOut:
        account_id = principal.sub
        return await self.account_reader.get(account_id=account_id)
