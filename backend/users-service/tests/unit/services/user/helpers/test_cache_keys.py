import uuid

from app.services.user.helpers.cache_keys import (
    account_cache_key,
    profile_cache_key,
    reactivation_cache_key,
    reset_password_cache_key,
)


def test_account_cache_key():
    account_id = uuid.UUID("c42b2c19-efda-4f42-a7e5-1e69190f51e0")

    result = account_cache_key(account_id)

    assert result == "account:c42b2c19-efda-4f42-a7e5-1e69190f51e0"


def test_profile_cache_key():
    account_id = uuid.UUID("c42b2c19-efda-4f42-a7e5-1e69190f51e0")

    result = profile_cache_key(account_id)

    assert result == "profile:c42b2c19-efda-4f42-a7e5-1e69190f51e0"


def test_reactivation_cache_key():
    token_hash = "abc123hash"

    result = reactivation_cache_key(token_hash)

    assert result == "auth:reactivation:abc123hash"


def test_reset_password_cache_key():
    token_hash = "xyz789hash"

    result = reset_password_cache_key(token_hash)

    assert result == "auth:reset-password:xyz789hash"
