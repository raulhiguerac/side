from app.core.exceptions.account import AccountNotFoundError 
from app.services.user.ports.account_repository import AccountRepository
from app.services.shared.adapters.sql_account_reader import SqlAccountReader


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
