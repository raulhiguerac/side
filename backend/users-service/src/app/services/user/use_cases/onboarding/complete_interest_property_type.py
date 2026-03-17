import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.user import (
    OnboardingCityInterestNotFoundError,
    PropertyTypeNotAllowedError,
)
from app.models.account import OnboardingStep
from app.models.interests import PropertyType, UserPropertyTypeInterest
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_invalidation import invalidate_current_user_cache
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork

_ALLOWED_PROPERTY_TYPES = {pt.value for pt in PropertyType}


class CompletePropertyTypeInterestUseCase:
    def __init__(
        self,
        *,
        uow: UserUnitOfWork,
        cache: CachePort,
        profile_reader: CurrentProfileReader,
    ) -> None:
        self.uow = uow
        self.cache = cache
        self.profile_reader = profile_reader

    async def execute(self, *, account_id: uuid.UUID, locality_id: uuid.UUID, property_type: list[str]) -> None:
        if not property_type:
            return

        for pt in property_type:
            if pt not in _ALLOWED_PROPERTY_TYPES:
                raise PropertyTypeNotAllowedError(value=pt)

        account = await self.uow.accounts.get_by_id(account_id=account_id)

        user_interest_id = await run_in_threadpool(
            partial(
                self.uow.onboarding.get_interest_by_account_locality,
                account_id=account.account_id,
                locality_id=locality_id,
            )
        )

        if user_interest_id is None:
            raise OnboardingCityInterestNotFoundError(account_id=account_id, locality_id=locality_id)

        property_list = [
            UserPropertyTypeInterest(
                user_interest_id=user_interest_id,
                property_type=pt,
            )
            for pt in property_type
        ]

        if account.onboarding_step == OnboardingStep.property_type:
            profile = await self.profile_reader.get_model(
                account_id=account_id,
                account_type=account.account_type,
            )

            await run_in_threadpool(
                partial(
                    self.uow.onboarding.mark_completed,
                    account_id=account.account_id,
                    key=OnboardingStep.property_type,
                )
            )

            account.onboarding_step = OnboardingStep.done
            profile.profile_score += 10

        await run_in_threadpool(
            partial(
                self.uow.onboarding.save_property_type,
                properties=property_list,
            )
        )

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise exc

        await invalidate_current_user_cache(self.cache, account_id)
