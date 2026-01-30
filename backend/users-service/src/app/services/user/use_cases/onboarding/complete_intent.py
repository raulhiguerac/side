import uuid

from app.models.account import OnboardingStep
from app.services.shared.ports.cache import CachePort
from app.services.user.helpers.cache_keys import account_cache_key, profile_cache_key
from app.services.user.helpers.current_profile_reader import CurrentProfileReader
from app.services.user.ports.unit_of_work import UserUnitOfWork
from app.services.user.schemas.onboarding import OnboardingIntent


class CompleteOnboardingIntentUseCase:
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

    async def execute(self, *, account_id: uuid.UUID, req: OnboardingIntent) -> None:
        account = await self.uow.accounts.get_by_id(account_id=account_id)

        if account.onboarding_step != OnboardingStep.intent:
            return

        profile = await self.profile_reader.get_model(
            account_id=account_id,
            account_type=account.account_type,
        )

        first_time = await self.uow.onboarding.mark_completed(
            account_id=account.account_id,
            key=OnboardingStep.intent,
        )

        if first_time:
            account.onboarding_step = OnboardingStep.city
            profile.profile_score += 10

        profile.intent = req.intent

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