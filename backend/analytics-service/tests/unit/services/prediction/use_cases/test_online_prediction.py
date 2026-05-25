import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.prediction import PredictionPersistenceError
from app.models.prediction import PropertyType
from app.services.prediction.schemas.prediction import PredictionRequest
from app.services.prediction.use_cases.online import OnlinePrediction

PRINCIPAL = uuid.uuid4()
PROP_ID = uuid.uuid4()

REQ = PredictionRequest(
    area_m2=80.0,
    bedrooms=2,
    bathrooms=1.0,
    parking_spots=1,
    stratum=4,
    property_type=PropertyType.apartment,
    lat=4.65,
    lon=-74.05,
    barrio_ideca="CHAPINERO",
    property_id=PROP_ID,
)


async def _fake_threadpool(func):
    return func()


def make_uc():
    model = MagicMock()
    model.online_predict.return_value = (500_000_000.0, "v1")

    uow = MagicMock()
    uow.prediction = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    return OnlinePrediction(uow=uow, model=model), uow, model


@pytest.mark.asyncio
async def test_happy_path_returns_response():
    uc, uow, _ = make_uc()
    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        response = await uc.execute(principal=PRINCIPAL, req=REQ)

    assert response.predicted_price == 500_000_000.0
    assert response.model_version == "v1"
    assert isinstance(response.id, uuid.UUID)
    assert response.created_at is not None


@pytest.mark.asyncio
async def test_happy_path_commits_and_does_not_rollback():
    uc, uow, _ = make_uc()
    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        await uc.execute(principal=PRINCIPAL, req=REQ)

    uow.commit.assert_awaited_once()
    uow.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_persistence_error_triggers_rollback():
    uc, uow, _ = make_uc()
    uow.commit.side_effect = Exception("db down")

    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        with pytest.raises(PredictionPersistenceError):
            await uc.execute(principal=PRINCIPAL, req=REQ)

    uow.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_persistence_error_wraps_cause():
    uc, uow, _ = make_uc()
    cause = Exception("constraint")
    uow.commit.side_effect = cause

    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        with pytest.raises(PredictionPersistenceError) as exc_info:
            await uc.execute(principal=PRINCIPAL, req=REQ)

    assert exc_info.value.cause is cause


@pytest.mark.asyncio
async def test_persistence_error_logs():
    uc, uow, _ = make_uc()
    uow.commit.side_effect = Exception("db down")

    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        with patch("app.services.prediction.use_cases.online.logger") as mock_logger:
            with pytest.raises(PredictionPersistenceError):
                await uc.execute(principal=PRINCIPAL, req=REQ)

    mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_model_receives_req_without_property_id():
    uc, _, model = make_uc()
    with patch("app.services.prediction.use_cases.online.run_in_threadpool", new=_fake_threadpool):
        await uc.execute(principal=PRINCIPAL, req=REQ)

    call_kwargs = model.online_predict.call_args[1]
    assert call_kwargs["record"] is REQ
