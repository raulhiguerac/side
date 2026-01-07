import uuid
from sqlmodel import Session

from app.schemas.auth import Principal
from app.schemas.user import CurrentUserOut

from app.repositories.account_repository import get_active_account_by_id

from app.core.exceptions.auth import InvalidTokenException
from app.core.exceptions.user import AccountNotFoundError


async def get_current_account_service(session: Session, principal: Principal) -> CurrentUserOut:
    try:
        account_id = uuid.UUID(principal.sub)
    except ValueError:
        raise InvalidTokenException("Invalid subject (sub) claim")
     
    curerent_account = get_active_account_by_id(session,account_id)
    if not curerent_account:
        raise AccountNotFoundError(account_id=account_id, email=getattr(principal, "email", None))
    
    return CurrentUserOut.model_validate(curerent_account)
