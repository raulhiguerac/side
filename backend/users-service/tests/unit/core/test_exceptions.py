import pytest

from app.core.exceptions.base import BaseError


def test_base_error_with_defaults():
    error = BaseError()

    assert error.message == "An unexpected error occurred"
    assert error.code == "INTERNAL_ERROR"
    assert error.context == {}
    assert error.cause is None
    assert str(error) == "An unexpected error occurred"


def test_base_error_with_custom_values():
    cause = ValueError("original error")
    error = BaseError(
        message="Custom error message",
        code="CUSTOM_ERROR",
        context={"key": "value"},
        cause=cause,
    )

    assert error.message == "Custom error message"
    assert error.code == "CUSTOM_ERROR"
    assert error.context == {"key": "value"}
    assert error.cause is cause


def test_base_error_is_exception():
    error = BaseError(message="Test")

    assert isinstance(error, Exception)

    with pytest.raises(BaseError):
        raise error
