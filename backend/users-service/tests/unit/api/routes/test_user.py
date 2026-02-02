import io
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import Response, UploadFile
from pydantic import TypeAdapter

from app.api.routes.user import (
    get_current_user,
    get_current_user_profile,
    update_user_profile,
    upload_user_profile_photo,
    deactivate_user_account,
    request_account_reactivation,
    confirm_account_reactivation,
)

from app.models.account import AccountIntent

from app.schemas.common import Principal
from app.services.user.schemas.current import CurrentUserOut, CurrentUserProfileOut
from app.services.user.schemas.photo import PhotoUploadOut
from app.services.user.schemas.reactivation import RequestReactivationIn
from app.services.user.schemas.update import UpdateRequest
from app.services.auth.schemas.tokens import RefreshToken

ACCOUNT_ID = uuid.UUID("c42b2c19-efda-4f42-a7e5-1e69190f51e0")

PROFILE_DATA = [
    {
        "first_name": "pepito",
        "last_name": "perez",
        "phone": "1234567890",
        "photo_url": "https://s3.micasaenminutos/abc/images/abc",
        "description": "Descripción de prueba",
        "intent": AccountIntent.buyer,
        "account_type": "person",
    },
    {
        "display_name": "inmobiliaria fake",
        "phone": "1234567890",
        "photo_url": "https://s3.micasaenminutos/abc/images/abc",
        "description": "Descripción de prueba",
        "intent": AccountIntent.seller,
        "account_type": "organization",
    },
]

PROFILE_ADAPTER = TypeAdapter(CurrentUserProfileOut)

UPDATED_DATA = [
    {
        "phone": "1234567890",
        "description": "Descripción de prueba",
        "intent": AccountIntent.buyer,
        "account_type": "person",
    },
    {
        "phone": "1234567890",
        "description": "Descripción de prueba",
        "intent": AccountIntent.buyer,
        "account_type": "organization",
    },
]

UPDATE_ADAPTER = TypeAdapter(UpdateRequest)

REFRESH_TOKEN_OBJECTS = [
    RefreshToken(refresh_token="abc"),
    None
]

@pytest.fixture
def response() -> Response:
    return Response()

@pytest.fixture
def principal() -> Principal:
    return Principal(
        sub=ACCOUNT_ID,
        email="pepito@micasaenminutos.com",
        email_verified=False,
        scope=["users-ms"],
    )

@pytest.mark.asyncio
async def test_get_current_user_and_return_model(principal):

    expected = CurrentUserOut(
        account_id= ACCOUNT_ID,
        email= principal.email,
        account_type= "person",
        onboarding_step= "intent",
        is_active= True
    )

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=expected)

    result = await get_current_user(principal=principal, uc=uc)

    uc.execute.assert_awaited_once_with(principal=principal)
    assert result == expected
    assert isinstance(result, CurrentUserOut)

@pytest.mark.asyncio
@pytest.mark.parametrize("profile_data", PROFILE_DATA)
async def test_get_current_user_profile_returns_current_user_profile_out(profile_data,principal):

    expected = PROFILE_ADAPTER.validate_python({
        "profile": profile_data
    })

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=expected)

    result = await get_current_user_profile(principal=principal, uc=uc)

    uc.execute.assert_awaited_once_with(account_id=principal.sub)
    assert result == expected
    assert isinstance(result, CurrentUserProfileOut)

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "profile_data, updated_data",
    list(zip(PROFILE_DATA, UPDATED_DATA)),
)
async def test_update_user_profile_and_returns_current_user_profile_out(profile_data,updated_data,principal):
    
    req = UPDATE_ADAPTER.validate_python(updated_data)

    merged = {**profile_data, **updated_data}
    expected = PROFILE_ADAPTER.validate_python({"profile": merged})

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=expected)

    result = await update_user_profile(req=req, principal=principal, uc=uc)

    uc.execute.assert_awaited_once_with(principal=principal, req=req)
    assert req.model_dump(exclude_unset=True) == updated_data
    assert isinstance(result, CurrentUserProfileOut)

@pytest.mark.asyncio
async def test_upload_user_profile_photo(principal):

    file = UploadFile(
        filename="avatar.png",
        file=io.BytesIO(b"fake-bytes"),
    )

    validated_mime = 'image/jpeg'

    expected = PhotoUploadOut(photo_url="https://s3.micasaenminutos/abc/images/abc")

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=expected)

    result = await upload_user_profile_photo(
        file=file,
        validated_mime=validated_mime,
        principal=principal,
        uc=uc,
    )

    uc.execute.assert_awaited_once()
    assert uc.execute.await_args.kwargs["file"] is file.file
    assert uc.execute.await_args.kwargs["content_type"] == validated_mime
    assert uc.execute.await_args.kwargs["principal"] == principal

    assert result == expected
    assert isinstance(result, PhotoUploadOut)

@pytest.mark.asyncio
@pytest.mark.parametrize("refresh", REFRESH_TOKEN_OBJECTS)
async def test_deactivate_user_account(principal, refresh):
    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    uc_logout = AsyncMock()
    uc_logout.logout = AsyncMock(return_value=None)

    result = await deactivate_user_account(
        principal=principal,
        refresh=refresh,
        uc=uc,
        uc_logout=uc_logout,
    )

    uc.execute.assert_awaited_once_with(principal=principal)
    uc_logout.logout.assert_awaited_once()

    expected_refresh_token = refresh.refresh_token if refresh else None
    assert uc_logout.logout.await_args.kwargs["refresh_token"] == expected_refresh_token

    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize("refresh", REFRESH_TOKEN_OBJECTS)
async def test_deactivate_user_account_succeeds_even_if_logout_fails(principal, refresh):
    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    uc_logout = AsyncMock()
    uc_logout.logout = AsyncMock(side_effect=Exception("boom"))

    result = await deactivate_user_account(
        principal=principal,
        refresh=refresh,
        uc=uc,
        uc_logout=uc_logout,
    )

    uc.execute.assert_awaited_once_with(principal=principal)

    uc_logout.logout.assert_awaited_once()
    expected_refresh_token = refresh.refresh_token if refresh else None
    assert uc_logout.logout.await_args.kwargs["refresh_token"] == expected_refresh_token

    assert result is None

@pytest.mark.asyncio
async def test_request_account_reactivation_calls_uc_and_returns_idempotent_message():
    req = RequestReactivationIn(email="pepito@micasaenminutos.com")

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    result = await request_account_reactivation(req=req, uc=uc)

    uc.execute.assert_awaited_once_with(email=req.email)
    assert result == {
        "message": "If the account exists, a reactivation email will be sent shortly."
    }


@pytest.mark.asyncio
async def test_confirm_account_reactivation_calls_uc_and_returns_success_message():
    token = "abcd"

    uc = AsyncMock()
    uc.execute = AsyncMock(return_value=None)

    result = await confirm_account_reactivation(token=token, uc=uc)

    uc.execute.assert_awaited_once_with(token=token)
    assert result == {"status": "reactivated"}
