from typing import Protocol

from app.models.account import CompanyProfile, UserProfile


class ProfileWriter(Protocol):
    async def create_profile(self, *, profile: UserProfile | CompanyProfile) -> UserProfile | CompanyProfile: ...