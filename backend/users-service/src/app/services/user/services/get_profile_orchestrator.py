import uuid

from app.services.user.schemas.current import CurrentUserProfileOut

from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.helpers.current_account_reader import CurrentAccountReader



class ProfileApplicationService:
    """
    Orchestrates profile resolution for an account.

    - get_profile(...)           -> allows inactive accounts
    - get_active_profile(...)    -> requires active account
    """

    def __init__(
        self,
        profile_reader: CurrentProfileReader,
        account_reader: CurrentAccountReader,
    ) -> None:
        self.profile_reader = profile_reader
        self.account_reader = account_reader

    async def get_profile(
        self,
        *,
        account_id: uuid.UUID,
    ) -> CurrentUserProfileOut:
        """
        Returns the profile for an account regardless of active status.
        Useful for:
        - reactivation flows
        - public views
        - admin access
        """
        return await self._get_profile(
            account_id=account_id,
            require_active=False,
        )

    async def get_active_profile(
        self,
        *,
        account_id: uuid.UUID,
    ) -> CurrentUserProfileOut:
        """
        Returns the profile only if the account is active.
        Used for authenticated user flows.
        """
        return await self._get_profile(
            account_id=account_id,
            require_active=True,
        )

    async def _get_profile(
        self,
        *,
        account_id: uuid.UUID,
        require_active: bool,
    ) -> CurrentUserProfileOut:
        cached = await self.profile_reader.get_from_cache(
            account_id=account_id
        )
        if cached:
            return cached

        if require_active:
            account = await self.account_reader.get_active(
                account_id=account_id
            )
        else:
            account = await self.account_reader.get(
                account_id=account_id
            )

        return await self.profile_reader.get(
            account_id=account_id,
            account_type=account.account_type,
        )