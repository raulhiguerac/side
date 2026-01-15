import uuid

from sqlmodel import Session
from app.repositories.account_repository import (
    get_account_by_email,
    get_account_by_id,
    create_account,
    create_profile,
)

from app.core.logging.logger import get_logger

logger = get_logger(__name__)

class SqlUnitOfWork:
    """
    UoW minimalista:
    - expone operaciones que ya tienes en repos
    - maneja commit/rollback
    """
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str):
        return get_account_by_email(self.session, email)
    
    def get_by_id(self, account_id: uuid.UUID):
        return get_account_by_id(self.session, account_id)

    def add_account(self, account):
        return create_account(self.session, account)

    def add_profile(self, profile):
        return create_profile(self.session, profile)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def safe_rollback(self, *, kc_user_id=None):
        try:
            self.rollback()
        except Exception:
            logger.exception(
                "db_rollback_failed",
                extra={"extra": {"kc_user_id": str(kc_user_id) if kc_user_id else None}},
            )
