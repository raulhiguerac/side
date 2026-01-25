from typing import Protocol

from app.models.account import UserProfile, CompanyProfile

class ProfileWriter(Protocol):
    async def create_profile(self, *, profile: UserProfile | CompanyProfile) -> UserProfile | CompanyProfile: ...