import pytest
from unittest.mock import patch

def test_settings_loads_front_base_url():
    with patch.dict("os.environ", {"FRONT_BASE_URL": "https://example.com"}, clear=False):
        from importlib import reload
        import app.core.config.settings as settings_module
        # Note: Settings is instantiated at import time, so we test the class directly
        from app.core.config.settings import Settings

        with patch.dict("os.environ", {"FRONT_BASE_URL": "https://test.com"}):
            s = Settings()
            assert s.FRONT_BASE_URL == "https://test.com"


def test_settings_cache_ttl_default():
    with patch.dict("os.environ", {"FRONT_BASE_URL": "https://example.com"}, clear=False):
        from app.core.config.settings import Settings

        with patch.dict("os.environ", {"FRONT_BASE_URL": "https://test.com"}):
            s = Settings()
            assert s.CACHE_REACTIVATION_TTL_SECONDS == 900


def test_settings_cache_ttl_custom():
    with patch.dict("os.environ", {
        "FRONT_BASE_URL": "https://example.com",
        "CACHE_REACTIVATION_TTL_SECONDS": "1800"
    }):
        from app.core.config.settings import Settings
        s = Settings()
        assert s.CACHE_REACTIVATION_TTL_SECONDS == 1800
