import pytest
from unittest.mock import AsyncMock

from app.services.auth.services.reset_password_mailer import (
    ResetPasswordMailer,
    RESET_PASSWORD_TEMPLATE_ID,
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
    name = "Pepito"
    redirect_url = "https://example.com/reset?token=abc123"

    email_sender.send_template_email.return_value = None

    await mailer.send_reset_password_email(
        email=email,
        name=name,
        redirect_url=redirect_url,
    )

    email_sender.send_template_email.assert_awaited_once_with(
        template_id=RESET_PASSWORD_TEMPLATE_ID,
        to=[{"email": email}],
        params={
            "name": name,
            "redirect_url": redirect_url,
        },
        tags=["reset-password"],
    )


@pytest.mark.asyncio
async def test_send_reset_password_email_uses_correct_template_id(mailer, email_sender):
    await mailer.send_reset_password_email(
        email="test@example.com",
        name="Test",
        redirect_url="https://example.com/reset",
    )

    call_kwargs = email_sender.send_template_email.call_args.kwargs
    assert call_kwargs["template_id"] == 2  # RESET_PASSWORD_TEMPLATE_ID
