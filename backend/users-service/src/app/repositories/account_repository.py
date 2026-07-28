import uuid
from typing import TypeVar

from sqlmodel import Session, select

from app.models.account import Account, CompanyProfile, UserProfile

TProfile = TypeVar("TProfile", UserProfile, CompanyProfile)

def get_account_by_email(session: Session, email: str) -> Account | None:
    statement = select(Account).where(Account.email == email)
    session_user = session.exec(statement).first()
    return session_user

def get_account_by_id(session: Session, account_id: uuid.UUID) -> Account | None:
    statement = select(Account).where(
        Account.account_id == account_id,
    )
    return session.exec(statement).first()

def get_active_account_profile(session: Session, account_id: uuid.UUID) -> TProfile:
    statement = select(TProfile).where(
        Account.account_id == account_id,
        Account.is_active.is_(True),
    )
    return session.exec(statement).first()

def get_active_accounts_bulk(session: Session, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
    statement = select(Account.account_id,Account.email).where(
        Account.email.in_(emails),
        Account.is_active.is_(True),
    )
    return session.exec(statement).all()