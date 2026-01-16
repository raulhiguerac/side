from app.core.logging.logger import get_logger
from app.schemas.auth import Principal, ChangePassword

from app.services.auth.ports.identity_provider import IdentityProvider
from app.services.auth.ports.authentication_provider import AuthenticationProvider
from app.services.shared.policies.active_account_policy import AccountActivePolicy

from app.core.exceptions.auth import SamePasswordNotAllowedError

logger = get_logger(__name__)


class ChangeAccountPasswordUseCase:
    def __init__(
        self,
        *,
        idp: IdentityProvider,
        auth_provider: AuthenticationProvider,
        account_policy: AccountActivePolicy,
    ):
        self.idp = idp
        self.auth_provider = auth_provider
        self.account_policy = account_policy

    async def change_password(self, *, principal: Principal, req: ChangePassword) -> None:
        if req.old_password == req.new_password:
            raise SamePasswordNotAllowedError()

        
        await self.account_policy.ensure_active_by_id(account_id=principal.sub)
        await self.auth_provider.login(email=principal.email, password=req.old_password)
        await self.idp.reset_password(account_id=principal.sub, new_password=req.new_password)

        logger.info(
            "password_change_ok",
            extra={"extra": {"account_id": str(principal.sub)}},
        )
