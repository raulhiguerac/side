import uuid

from app.schemas.user import CurrentUserProfileOut

from app.services.user.services.get_profile_orchestrator import ProfileApplicationService
from app.core.exceptions.user import AccountDisabledError

class GetCurrentProfileUseCase:
    def __init__(self, *, profile_service: ProfileApplicationService):
        self.profile_service = profile_service

    async def execute(self, *, account_id: uuid.UUID) -> CurrentUserProfileOut:
        return await self.profile_service.get_active_profile(account_id=account_id)        