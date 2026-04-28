import uuid
from sqlmodel import Session, select

from app.models.account import UserProfile, CompanyProfile

def get_user_profile_by_account_id(session: Session, account_id: uuid.UUID) -> UserProfile:
    statement = select(UserProfile).where(UserProfile.account_id == account_id)
    profile = session.exec(statement).first()
    return profile

def get_company_profile_by_account_id(session: Session, account_id: uuid.UUID) -> CompanyProfile:
    statement = select(CompanyProfile).where(CompanyProfile.account_id == account_id)
    profile = session.exec(statement).first()
    return profile