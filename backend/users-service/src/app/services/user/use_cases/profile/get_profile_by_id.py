import uuid

from app.services.user.schemas.current import CurrentUserProfileOut
from app.services.user.services.get_profile_orchestrator import (
    ProfileApplicationService,
)


class GetProfileByIdUseCase:
    def __init__(self, *, profile_service: ProfileApplicationService):
        self.profile_service = profile_service

    async def execute(self, *, account_id: uuid.UUID) -> CurrentUserProfileOut:
        return await self.profile_service.get_active_profile(account_id=account_id)
