import uuid

from sqlmodel import Session

from app.models.account import CompanyProfile, UserProfile
from app.repositories.user_repository import (
    get_company_profile_by_account_id,
    get_user_profile_by_account_id,
)
from app.services.user.ports.user_repository import UserRepository


class SqlUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user_profile_by_id(self, *, account_id: uuid.UUID) -> UserProfile:
        return get_user_profile_by_account_id(self._session, account_id)
    
    def get_company_profile_by_id(self, *, account_id: uuid.UUID) -> CompanyProfile:
        return get_company_profile_by_account_id(self._session, account_id)