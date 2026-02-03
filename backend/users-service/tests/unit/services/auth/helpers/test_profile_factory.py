import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import TypeAdapter

from app.models.account import AccountType, UserProfile, CompanyProfile
from app.services.auth.helpers.profile_factory import ProfileFactory
from app.services.auth.schemas.registration import RegisterRequest


PERSON_DATA = {
    "first_name": "Pepito",
    "last_name": "Perez",
    "email": "pepito@example.com",
    "password": "securepassword",
    "phone": "1234567890",
    "account_type": "person",
}

ORGANIZATION_DATA = {
    "display_name": "Test Company",
    "email": "company@example.com",
    "password": "securepassword",
    "phone": "9876543210",
    "account_type": "organization",
}

REGISTER_ADAPTER = TypeAdapter(RegisterRequest)


@pytest.fixture
def factory():
    return ProfileFactory()


def test_profile_factory_creates_user_profile(factory):
    req = REGISTER_ADAPTER.validate_python(PERSON_DATA)
    account_id = uuid.uuid4()

    result = factory.from_register(req=req, account_id=account_id)

    assert isinstance(result, UserProfile)
    assert result.account_id == account_id
    assert result.first_name == "Pepito"
    assert result.last_name == "Perez"
    assert result.phone == "1234567890"
    assert result.profile_score == 10


def test_profile_factory_creates_company_profile(factory):
    req = REGISTER_ADAPTER.validate_python(ORGANIZATION_DATA)
    account_id = uuid.uuid4()

    result = factory.from_register(req=req, account_id=account_id)

    assert isinstance(result, CompanyProfile)
    assert result.account_id == account_id
    assert result.display_name == "Test Company"
    assert result.phone == "9876543210"
    assert result.profile_score == 10
