import uuid
import pytest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.models.account import Account, UserProfile, OnboardingStep, AccountType


def _get_set_cookie_headers(response):
    return response.headers.get_list("set-cookie")


def _assert_auth_cookies_set(response):
    set_cookie = _get_set_cookie_headers(response)

    assert any(h.startswith("access_token=") for h in set_cookie), (
        f"No se seteó access_token cookie. set-cookie={set_cookie}"
    )
    assert any(h.startswith("refresh_token=") for h in set_cookie), (
        f"No se seteó refresh_token cookie. set-cookie={set_cookie}"
    )

    assert any("HttpOnly" in h for h in set_cookie), (
        f"Cookies deberían ser HttpOnly. set-cookie={set_cookie}"
    )
    assert any("Path=/" in h for h in set_cookie), (
        f"Cookies deberían tener Path=/. set-cookie={set_cookie}"
    )


def _assert_auth_cookies_cleared(response):
    set_cookie = _get_set_cookie_headers(response)

    access = [h for h in set_cookie if h.startswith("access_token=")]
    refresh = [h for h in set_cookie if h.startswith("refresh_token=")]

    assert access, f"Logout no tocó access_token cookie. set-cookie={set_cookie}"
    assert refresh, f"Logout no tocó refresh_token cookie. set-cookie={set_cookie}"

    assert any("Max-Age=0" in h or "expires=" in h.lower() for h in access), (
        f"access_token no parece expirada. {access}"
    )
    assert any("Max-Age=0" in h or "expires=" in h.lower() for h in refresh), (
        f"refresh_token no parece expirada. {refresh}"
    )


class TestPersonUserJourney:
    def test_register_persists_account_and_profile_and_calls_idp(
        self,
        client: TestClient,
        test_session,
        person_register_data: dict,
        mock_identity_provider: AsyncMock,
    ):
        res = client.post("/v1/auth/register", json=person_register_data)

        assert res.status_code == 201, f"Registro falló: {res.status_code} {res.json()}"
        body = res.json()
        assert "account_id" in body
        assert body["email"] == person_register_data["email"]

        account_id = uuid.UUID(body["account_id"])

        account = test_session.get(Account, account_id)
        assert account is not None, "Account no fue creada en la DB"
        assert account.email == person_register_data["email"]
        assert account.account_type == AccountType.person
        assert account.is_active is True
        assert account.onboarding_step == OnboardingStep.intent  # enum

        profile = test_session.get(UserProfile, account_id)
        assert profile is not None, "UserProfile no fue creado en la DB"
        assert profile.first_name == person_register_data["first_name"]
        assert profile.last_name == person_register_data["last_name"]

        mock_identity_provider.create_account.assert_called_once()
        kwargs = mock_identity_provider.create_account.call_args.kwargs
        assert kwargs.get("email") == person_register_data["email"]

    def test_login_sets_auth_cookies(
        self,
        client: TestClient,
        person_register_data: dict,
        mock_auth_provider: AsyncMock,
    ):
        reg = client.post("/v1/auth/register", json=person_register_data)
        assert reg.status_code == 201, f"Registro falló: {reg.status_code} {reg.json()}"

        login = client.post(
            "/v1/auth/login",
            json={
                "email": person_register_data["email"],
                "password": person_register_data["password"],
            },
        )

        assert login.status_code == 200, f"Login falló: {login.status_code} {login.json()}"
        assert login.json().get("message") == "ok"

        mock_auth_provider.login.assert_called_once()

        _assert_auth_cookies_set(login)

    def test_logout_clears_auth_cookies(
        self,
        client: TestClient,
        person_register_data: dict,
        mock_auth_provider: AsyncMock,
    ):
        reg = client.post("/v1/auth/register", json=person_register_data)
        assert reg.status_code == 201

        login = client.post(
            "/v1/auth/login",
            json={
                "email": person_register_data["email"],
                "password": person_register_data["password"],
            },
        )
        assert login.status_code == 200
        _assert_auth_cookies_set(login)

        out = client.post("/v1/auth/logout")

        assert out.status_code == 204, f"Logout falló: {out.status_code} {out.text}"
        mock_auth_provider.logout.assert_called_once()
        _assert_auth_cookies_cleared(out)


class TestOrganizationUserJourney:
    def test_organization_registration_persists_company_profile(
        self,
        client: TestClient,
        test_session,
        organization_register_data: dict,
    ):
        res = client.post("/v1/auth/register", json=organization_register_data)
        assert res.status_code == 201, f"Registro org falló: {res.status_code} {res.json()}"

        account_id = uuid.UUID(res.json()["account_id"])

        account = test_session.get(Account, account_id)
        assert account is not None
        assert account.account_type == AccountType.organization

        from app.models.account import CompanyProfile
        profile = test_session.get(CompanyProfile, account_id)
        assert profile is not None
        assert profile.display_name == organization_register_data["display_name"]


class TestUserJourneyErrors:
    def test_register_duplicate_email_returns_409(
        self,
        client: TestClient,
        person_register_data: dict,
    ):
        first = client.post("/v1/auth/register", json=person_register_data)
        assert first.status_code == 201

        second = client.post("/v1/auth/register", json=person_register_data)
        assert second.status_code == 409

    def test_login_wrong_password_returns_401(
        self,
        client: TestClient,
        person_register_data: dict,
        mock_auth_provider: AsyncMock,
    ):
        from app.core.exceptions.auth import InvalidCredentialsError

        client.post("/v1/auth/register", json=person_register_data)

        mock_auth_provider.login.side_effect = InvalidCredentialsError()

        res = client.post(
            "/v1/auth/login",
            json={
                "email": person_register_data["email"],
                "password": "WrongPassword123!",
            },
        )
        assert res.status_code == 401

    def test_access_protected_route_without_auth_returns_401(self, client: TestClient):
        from app.api.deps.auth import get_current_principal

        client.app.dependency_overrides.pop(get_current_principal, None)

        res = client.get("/v1/users/me")
        assert res.status_code == 401


class TestDataValidation:
    def test_register_invalid_email_returns_422(self, client: TestClient):
        res = client.post(
            "/v1/auth/register",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "not-an-email",
                "password": "SecurePassword123!",
                "account_type": "person",
            },
        )
        assert res.status_code == 422

    def test_register_missing_required_field_returns_422(self, client: TestClient):
        res = client.post(
            "/v1/auth/register",
            json={
                "first_name": "Test",
                "account_type": "person",
            },
        )
        assert res.status_code == 422
        assert "detail" in res.json()