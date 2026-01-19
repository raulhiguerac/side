import uuid

from app.schemas.auth import Principal
from app.schemas.user import CurrentUserProfileOut

from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.helpers.current_account_reader import CurrentAccountReader

from app.core.exceptions.auth import InvalidTokenException

class ProfileApplicationService:
    def __init__(self, profile_reader: CurrentProfileReader, account_reader: CurrentAccountReader):
        self.profile_reader = profile_reader
        self.account_reader = account_reader

    async def get_profile(self, principal: Principal) -> CurrentUserProfileOut:
        account_id = principal.sub
        if not isinstance(principal.sub, uuid.UUID):
            raise InvalidTokenException("Invalid subject (sub) claim")
        
        cached = await self.profile_reader.get_from_cache(account_id=account_id)
        if cached:
            return cached

        account = await self.account_reader.get(account_id=account_id)

        return await self.profile_reader.get(
            account_id=account_id,
            account_type=account.account_type,
        )