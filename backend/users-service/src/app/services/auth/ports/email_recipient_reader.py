import uuid
from typing import Protocol, Optional
from app.models.account import AccountType

class EmailRecipientReaderPort(Protocol):
    async def get_display_name_by_account_id(
        self,
        *,
        account_id: uuid.UUID,
        account_type: AccountType
    ) -> Optional[str]: ...