import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.account import OnboardingStep
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_invalidation import invalidate_current_user_cache
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork


class CompleteCityIntentUseCase:
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

    async def execute(self, *, account_id: uuid.UUID, locality_id: uuid.UUID) -> None:
        account = await self.uow.accounts.get_by_id(account_id=account_id)

        if account.onboarding_step == OnboardingStep.city:
            profile = await self.profile_reader.get_model(
                account_id=account_id,
                account_type=account.account_type,
            )

            await run_in_threadpool(
                partial(
                    self.uow.onboarding.mark_completed,
                    account_id=account.account_id,
                    key=OnboardingStep.city,
                )
            )

            account.onboarding_step = OnboardingStep.neighborhood
            profile.profile_score += 10
            
        await run_in_threadpool(
            partial(
                self.uow.onboarding.save_locality,
                account_id=account_id,
                locality_id=locality_id,
            )
        )

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise exc

        await invalidate_current_user_cache(self.cache, account_id)
