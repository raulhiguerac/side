import uuid
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.core.exceptions.user import (
    NeighborhoodRankOutOfRangeError,
    OnboardingCityInterestNotFoundError,
)
from app.models.account import OnboardingStep
from app.models.interests import UserNeighborhoodInterest
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_invalidation import invalidate_current_user_cache
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

    async def execute(
        self,
        *,
        account_id: uuid.UUID,
        localities: list[dict],
    ) -> None:
        account = await self.uow.accounts.get_by_id(account_id=account_id)

        neighborhoods_list: list[UserNeighborhoodInterest] = []

        for item in localities:
            locality_id = item["locality_id"]
            neighborhoods = item["neighborhoods"]

            user_interest_id = await run_in_threadpool(
                partial(
                    self.uow.onboarding.get_interest_by_account_locality,
                    account_id=account.account_id,
                    locality_id=locality_id,
                )
            )

            if user_interest_id is None:
                raise OnboardingCityInterestNotFoundError(account_id=account_id, locality_id=locality_id)

            for rank in neighborhoods:
                if not (1 <= rank <= 5):
                    raise NeighborhoodRankOutOfRangeError(rank=rank)

            neighborhoods_list.extend(
                UserNeighborhoodInterest(
                    user_interest_id=user_interest_id,
                    neighborhood_id=neighborhood_id,
                    interest_rank=rank,
                )
                for rank, neighborhood_id in neighborhoods.items()
            )

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

        await invalidate_current_user_cache(self.cache, account_id)
