import uuid

from app.services.shared.ports.account_reader import AccountReaderPort


class ResolveAccountsBulkUseCase:
    def __init__(self, *, account_reader: AccountReaderPort) -> None:
        self.account_reader = account_reader

    async def execute(self, *, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        return await self.account_reader.get_accounts_bulk(emails=emails)
