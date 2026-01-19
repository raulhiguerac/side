import uuid

from app.schemas.auth import Principal
from app.schemas.user import CurrentUserProfileOut

from app.services.user.services.get_profile_orchestrator import ProfileApplicationService

class GetCurrentProfileUseCase:
    def __init__(self, *, profile_service: ProfileApplicationService):
        self.profile_service = profile_service

    async def execute(self, principal: Principal) -> CurrentUserProfileOut:
        return await self.profile_service.get_profile(principal=principal)