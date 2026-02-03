import uuid
import pytest
from unittest.mock import AsyncMock

from app.schemas.common import Principal
from app.models.account import OnboardingStep
from app.services.user.schemas.onboarding import OnboardingIntent
from app.api.routes.onboarding import select_onboarding_intent


@pytest.fixture
def principal():
    return Principal(
        sub=uuid.uuid4(),
        email="pepito@micasaenminutos.com",
        email_verified=True,
        scope=["users-ms"],
    )


@pytest.fixture
def uc():
    return AsyncMock()


# Happy path
@pytest.mark.asyncio
async def test_select_onboarding_intent_success(principal, uc):
    req = OnboardingIntent(intent=OnboardingStep.intent)
    uc.execute.return_value = None

    result = await select_onboarding_intent(req=req, principal=principal, uc=uc)

    uc.execute.assert_awaited_once_with(account_id=principal.sub, req=req)
    assert result is None
