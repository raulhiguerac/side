import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.models.account import Account, AccountIntent, OnboardingStep
from app.services.user.helpers.cache_keys import (
    account_cache_key,
    interests_cache_key,
    profile_cache_key,
)
from app.services.user.schemas.onboarding import OnboardingIntent
from app.services.user.use_cases.onboarding.complete_intent import (
    CompleteOnboardingIntentUseCase,
)


@pytest.fixture
def uow():
    uow = AsyncMock()
    uow.onboarding.mark_completed = MagicMock()  # sync: runs in threadpool
    return uow


@pytest.fixture
def cache():
    return AsyncMock()


@pytest.fixture
def profile_reader():
    return AsyncMock()


@pytest.fixture
def uc(uow, cache, profile_reader):
    return CompleteOnboardingIntentUseCase(
        uow=uow,
        cache=cache,
        profile_reader=profile_reader,
    )


@pytest.fixture
def account_at_intent_step():
    return Account(
        account_id=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        account_type="person",
        onboarding_step=OnboardingStep.intent,
        is_active=True,
    )


@pytest.fixture
def account_past_intent_step():
    return Account(
        account_id=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        account_type="person",
        onboarding_step=OnboardingStep.city,  # Already past intent
        is_active=True,
    )


@pytest.fixture
def profile_db():
    profile = MagicMock()
    profile.intent = None
    profile.profile_score = 10
    return profile


# Happy path - first time completing intent
@pytest.mark.asyncio
async def test_complete_intent_first_time(
    uc, uow, cache, profile_reader, account_at_intent_step, profile_db
):
    req = OnboardingIntent(intent=AccountIntent.buyer)
    account_id = account_at_intent_step.account_id

    uow.accounts.get_by_id.return_value = account_at_intent_step
    profile_reader.get_model.return_value = profile_db
    uow.onboarding.mark_completed.return_value = True  # First time
    uow.commit.return_value = None
    cache.delete.return_value = None

    await uc.execute(account_id=account_id, req=req)

    uow.accounts.get_by_id.assert_awaited_once_with(account_id=account_id)
    profile_reader.get_model.assert_awaited_once()
    uow.onboarding.mark_completed.assert_called_once_with(
        account_id=account_id, key=OnboardingStep.intent
    )
    uow.commit.assert_awaited_once()

    # First time: step advances and score increases
    assert account_at_intent_step.onboarding_step == OnboardingStep.city
    assert profile_db.profile_score == 20
    assert profile_db.intent == AccountIntent.buyer

    # Cache invalidated
    cache.delete.assert_has_awaits(
        [
            call(profile_cache_key(account_id)),
            call(account_cache_key(account_id)),
            call(interests_cache_key(account_id)),
        ]
    )


# Not first time - only intent updated
@pytest.mark.asyncio
async def test_complete_intent_not_first_time(
    uc, uow, cache, profile_reader, account_at_intent_step, profile_db
):
    req = OnboardingIntent(intent=AccountIntent.seller)
    account_id = account_at_intent_step.account_id

    uow.accounts.get_by_id.return_value = account_at_intent_step
    profile_reader.get_model.return_value = profile_db
    uow.onboarding.mark_completed.return_value = False  # Not first time
    uow.commit.return_value = None
    cache.delete.return_value = None

    await uc.execute(account_id=account_id, req=req)

    # Not first time: step stays same, score not increased
    assert account_at_intent_step.onboarding_step == OnboardingStep.intent
    assert profile_db.profile_score == 10
    assert profile_db.intent == AccountIntent.seller


# Already past intent step - no-op
@pytest.mark.asyncio
async def test_complete_intent_already_past(
    uc, uow, cache, profile_reader, account_past_intent_step
):
    req = OnboardingIntent(intent=AccountIntent.buyer)
    account_id = account_past_intent_step.account_id

    uow.accounts.get_by_id.return_value = account_past_intent_step

    await uc.execute(account_id=account_id, req=req)

    uow.accounts.get_by_id.assert_awaited_once()
    profile_reader.get_model.assert_not_called()
    uow.onboarding.mark_completed.assert_not_called()
    uow.commit.assert_not_called()


# Commit fails - rollback
@pytest.mark.asyncio
async def test_complete_intent_commit_fails(
    uc, uow, cache, profile_reader, account_at_intent_step, profile_db
):
    req = OnboardingIntent(intent=AccountIntent.buyer)
    account_id = account_at_intent_step.account_id

    uow.accounts.get_by_id.return_value = account_at_intent_step
    profile_reader.get_model.return_value = profile_db
    uow.onboarding.mark_completed.return_value = True
    uow.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        await uc.execute(account_id=account_id, req=req)

    uow.rollback.assert_awaited_once()
    cache.delete.assert_not_called()


# Cache delete fails - silent (best-effort)
@pytest.mark.asyncio
async def test_complete_intent_cache_fails_silent(
    uc, uow, cache, profile_reader, account_at_intent_step, profile_db
):
    req = OnboardingIntent(intent=AccountIntent.buyer)
    account_id = account_at_intent_step.account_id

    uow.accounts.get_by_id.return_value = account_at_intent_step
    profile_reader.get_model.return_value = profile_db
    uow.onboarding.mark_completed.return_value = True
    uow.commit.return_value = None
    cache.delete.side_effect = Exception("Redis error")

    # Should not raise
    await uc.execute(account_id=account_id, req=req)

    uow.commit.assert_awaited_once()
