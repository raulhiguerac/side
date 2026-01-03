from typing import TypeVar
from sqlmodel import Session, select

from app.models.user import Accounts, UserProfile, CompanyProfile

TProfile = TypeVar("TProfile", UserProfile, CompanyProfile)

def get_user_by_email(session: Session, email: str) -> Accounts | None:
    statement = select(Accounts).where(Accounts.email == email)
    session_user = session.exec(statement).first()
    return session_user

def create_user_repo(session: Session, user: Accounts) -> Accounts:
    session.add(user)
    session.flush()
    return user

def create_user_profile(session: Session,profile: TProfile) -> TProfile:
    session.add(profile)
    session.flush()
    return profile