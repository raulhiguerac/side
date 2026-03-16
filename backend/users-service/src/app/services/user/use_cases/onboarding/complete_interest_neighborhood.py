import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.models.account import OnboardingStep
from app.models.interests import UserNeighborhoodInterest
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import account_cache_key, profile_cache_key
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork


class CompleteNeighborhoodInterestUseCase:
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

    async def execute(self, *, account_id: uuid.UUID, locality_id: uuid.UUID, neighborhoods: dict[int, uuid.UUID]) -> None:
        account = await self.uow.accounts.get_by_id(account_id=account_id)

        user_interest_id = await run_in_threadpool(
            partial(
                self.uow.onboarding.get_interest_by_account_locality,
                account_id=account.account_id,
                locality_id=locality_id,
            )
        )

        neighborhoods_list = [
            UserNeighborhoodInterest(
                user_interest_id=user_interest_id,
                neighborhood_id=neighborhood_id,
                interest_rank=rank,
            )
            for rank, neighborhood_id in neighborhoods.items()
        ]

        if account.onboarding_step == OnboardingStep.neighborhood:
            profile = await self.profile_reader.get_model(
                account_id=account_id,
                account_type=account.account_type,
            )

            await run_in_threadpool(
                partial(
                    self.uow.onboarding.mark_completed,
                    account_id=account.account_id,
                    key=OnboardingStep.neighborhood,
                )
            )

            account.onboarding_step = OnboardingStep.property_type
            profile.profile_score += 10

        await run_in_threadpool(
            partial(
                self.uow.onboarding.save_neighborhoods,
                neighborhoods=neighborhoods_list,
            )
        )

        try:
            await self.uow.commit()
        except Exception as exc:
            await self.uow.rollback()
            raise exc

        try:
            await self.cache.delete(profile_cache_key(account_id))
            await self.cache.delete(account_cache_key(account_id))
        except Exception:
            pass
