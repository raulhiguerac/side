import uuid
from typing import Protocol

from app.models.account import UserProfile, CompanyProfile

class UserRepository(Protocol):
    def get_user_profile_by_id(self, *, account_id: uuid.UUID) -> UserProfile: ...
    def get_company_profile_by_id(self, *, account_id: uuid.UUID) -> CompanyProfile: ...