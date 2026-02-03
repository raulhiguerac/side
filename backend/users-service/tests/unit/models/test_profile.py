import uuid

from app.models.account import (
    UserProfile,
    CompanyProfile,
    AccountIntent,
)


def test_user_profile_creation():
    account_id = uuid.uuid4()
    profile = UserProfile(
        account_id=account_id,
        first_name="Pepito",
        last_name="Perez",
        phone="1234567890",
        intent=AccountIntent.buyer,
        description="Test description",
        profile_score=10,
    )

    assert profile.account_id == account_id
    assert profile.first_name == "Pepito"
    assert profile.last_name == "Perez"
    assert profile.phone == "1234567890"
    assert profile.intent == AccountIntent.buyer
    assert profile.profile_score == 10
    assert profile.photo_url is None
    assert profile.photo_key is None


def test_user_profile_defaults():
    account_id = uuid.uuid4()
    profile = UserProfile(
        account_id=account_id,
        first_name="Test",
        last_name="User",
    )

    assert profile.phone is None
    assert profile.intent is None
    assert profile.photo_url is None
    assert profile.description is None
    assert profile.profile_score == 0


def test_company_profile_creation():
    account_id = uuid.uuid4()
    profile = CompanyProfile(
        account_id=account_id,
        display_name="Test Company",
        phone="9876543210",
        intent=AccountIntent.seller,
        description="A test company",
        profile_score=20,
    )

    assert profile.account_id == account_id
    assert profile.display_name == "Test Company"
    assert profile.phone == "9876543210"
    assert profile.intent == AccountIntent.seller
    assert profile.profile_score == 20


def test_company_profile_defaults():
    account_id = uuid.uuid4()
    profile = CompanyProfile(
        account_id=account_id,
        display_name="Minimal Company",
    )

    assert profile.phone is None
    assert profile.intent is None
    assert profile.photo_url is None
    assert profile.description is None
    assert profile.profile_score == 0
