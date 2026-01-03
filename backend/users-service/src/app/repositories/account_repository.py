from typing import TypeVar
from sqlmodel import Session, select

from app.models.account import Account, UserProfile, CompanyProfile

TProfile = TypeVar("TProfile", UserProfile, CompanyProfile)

def get_account_by_email(session: Session, email: str) -> Account | None:
    statement = select(Account).where(Account.email == email)
    session_user = session.exec(statement).first()
    return session_user

def create_account(session: Session, account: Account) -> Account:
    session.add(account)
    session.flush()
    return account

def create_profile(session: Session,profile: TProfile) -> TProfile:
    session.add(profile)
    session.flush()
    return profile