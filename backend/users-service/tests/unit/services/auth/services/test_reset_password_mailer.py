from unittest.mock import AsyncMock

import pytest

from app.services.auth.services.reset_password_mailer import (
    RESET_PASSWORD_SUBJECT,
    ResetPasswordMailer,
)


@pytest.fixture
def email_sender():
    return AsyncMock()


@pytest.fixture
def mailer(email_sender):
    return ResetPasswordMailer(email_sender=email_sender)


@pytest.mark.asyncio
async def test_send_reset_password_email(mailer, email_sender):
    email = "pepito@example.com"
    redirect_url = "https://example.com/reset?token=abc123"

    await mailer.send_reset_password_email(
        email=email,
        name="Pepito",
        redirect_url=redirect_url,
    )

    email_sender.send_email.assert_awaited_once()
    call_kwargs = email_sender.send_email.call_args.kwargs
    assert call_kwargs["to"] == [email]
    assert call_kwargs["subject"] == RESET_PASSWORD_SUBJECT
    assert redirect_url in call_kwargs["html_content"]
    assert redirect_url in call_kwargs["text_content"]
    assert "Pepito" in call_kwargs["text_content"]


@pytest.mark.asyncio
async def test_send_reset_password_email_escapes_name_in_html(mailer, email_sender):
    await mailer.send_reset_password_email(
        email="test@example.com",
        name="<b>Test</b>",
        redirect_url="https://example.com/reset",
    )

    call_kwargs = email_sender.send_email.call_args.kwargs
    assert "&lt;b&gt;Test&lt;/b&gt;" in call_kwargs["html_content"]
    assert "<b>Test</b>" not in call_kwargs["html_content"]
