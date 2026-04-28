
from app.schemas.common import Principal
from app.services.user.helpers.current_account_reader import CurrentAccountReader
from app.services.user.schemas.current import CurrentUserOut


class GetCurrentAccountUseCase:
    def __init__(self, *, account_reader: CurrentAccountReader) -> None:
        self.account_reader = account_reader

    async def execute(self, *, principal: Principal) -> CurrentUserOut:
        account_id = principal.sub
        return await self.account_reader.get_active(account_id=account_id)
