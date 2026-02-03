import uuid
from datetime import datetime

from app.models.account import (
    Account,
    AccountType,
    AccountActionActor,
    AccountDeactivationReason,
    OnboardingStep,
    AccountIntent,
)


def test_account_type_enum():
    assert AccountType.person == "person"
    assert AccountType.organization == "organization"


def test_account_action_actor_enum():
    assert AccountActionActor.user == "user"
    assert AccountActionActor.admin == "admin"
    assert AccountActionActor.system == "system"


def test_account_deactivation_reason_enum():
    assert AccountDeactivationReason.user_request == "user_request"
    assert AccountDeactivationReason.admin_ban == "admin_ban"
    assert AccountDeactivationReason.terms_violation == "terms_violation"


def test_onboarding_step_enum():
    assert OnboardingStep.intent == "intent"
    assert OnboardingStep.city == "city"
    assert OnboardingStep.neighborhood == "neighborhood"
    assert OnboardingStep.done == "done"


def test_account_intent_enum():
    assert AccountIntent.buyer == "buyer"
    assert AccountIntent.seller == "seller"
    assert AccountIntent.renter == "renter"
    assert AccountIntent.explorer == "explorer"


def test_account_model_creation():
    account_id = uuid.uuid4()
    account = Account(
        account_id=account_id,
        email="test@example.com",
        account_type=AccountType.person,
        onboarding_step=OnboardingStep.intent,
        is_active=True,
    )

    assert account.account_id == account_id
    assert account.email == "test@example.com"
    assert account.account_type == AccountType.person
    assert account.onboarding_step == OnboardingStep.intent
    assert account.is_active is True
    assert account.deactivated_at is None
    assert account.deactivated_by is None


def test_account_model_with_deactivation():
    account_id = uuid.uuid4()
    now = datetime.utcnow()

    account = Account(
        account_id=account_id,
        email="test@example.com",
        account_type=AccountType.organization,
        onboarding_step=OnboardingStep.done,
        is_active=False,
        deactivated_at=now,
        deactivated_by=AccountActionActor.admin,
        deactivation_reason=AccountDeactivationReason.terms_violation,
        deactivation_note="Violated terms of service",
    )

    assert account.is_active is False
    assert account.deactivated_at == now
    assert account.deactivated_by == AccountActionActor.admin
    assert account.deactivation_reason == AccountDeactivationReason.terms_violation
