from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.models.account import UserProfile, CompanyProfile
from app.services.auth.ports.profile_registration_writer import ProfileWriter


class SqlProfileRepository(ProfileWriter):
    def __init__(self, *, session: Session):
        self._session = session

    def _create(self, profile):
        self._session.add(profile)
        self._session.flush()
        return profile

    async def create_profile(self, *, profile: UserProfile | CompanyProfile) -> UserProfile | CompanyProfile:
        return await run_in_threadpool(self._create, profile)
