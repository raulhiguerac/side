from sqlmodel import Session, select

from app.models.user import User, UserProfile

def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user

def create_user_repo(session: Session, user: User) -> User:
    session.add(user)
    return user

def create_user_profile(session: Session, user: UserProfile) -> UserProfile:
    session.add(user)
    return user