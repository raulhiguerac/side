import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.prediction import PropertyType
from app.services.prediction.schemas.prediction import PredictionRequest
from app.services.prediction.use_cases.batch import BatchPrediction

PRINCIPAL = uuid.uuid4()
PROP_ID_1 = uuid.uuid4()
PROP_ID_2 = uuid.uuid4()


def make_req(prop_id=None):
    return PredictionRequest(
        area_m2=80.0,
        bedrooms=2,
        bathrooms=1.0,
        parking_spots=1,
        stratum=4,
        property_type=PropertyType.apartment,
        lat=4.65,
        lon=-74.05,
        barrio_ideca="CHAPINERO",
        property_id=prop_id,
    )


REQ1 = make_req(PROP_ID_1)
REQ2 = make_req(PROP_ID_2)


async def _fake_threadpool(func):
    return func()


def make_uc(prices=(500.0, 600.0), version="v1"):
    model = MagicMock()
    model.batch_predict.return_value = (list(prices), version)

    uow = MagicMock()
    uow.prediction = MagicMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.begin_nested = AsyncMock()
    uow.rollback_to_savepoint = AsyncMock()

    return BatchPrediction(uow=uow, model=model), uow, model


@pytest.mark.asyncio
async def test_bulk_insert_happy_path():
    uc, uow, _ = make_uc()
    with patch("app.services.prediction.use_cases.batch.run_in_threadpool", new=_fake_threadpool):
        result = await uc.execute(
            principal=PRINCIPAL,
            messages=[(PROP_ID_1, REQ1), (PROP_ID_2, REQ2)],
        )

    assert len(result.predictions) == 2
    assert result.failed == []
    uow.prediction.batch_add.assert_called_once()
    uow.commit.assert_awaited_once()
    uow.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_bulk_insert_returns_correct_ids_and_prices():
    uc, _, _ = make_uc(prices=(100.0, 200.0))
    with patch("app.services.prediction.use_cases.batch.run_in_threadpool", new=_fake_threadpool):
        result = await uc.execute(
            principal=PRINCIPAL,
            messages=[(PROP_ID_1, REQ1), (PROP_ID_2, REQ2)],
        )

    ids = [msg_id for msg_id, _ in result.predictions]
    assert PROP_ID_1 in ids
    assert PROP_ID_2 in ids


@pytest.mark.asyncio
async def test_bulk_failure_falls_back_to_row_by_row():
    uc, uow, _ = make_uc()
    uow.prediction.batch_add.side_effect = Exception("unique violation")

    with patch("app.services.prediction.use_cases.batch.run_in_threadpool", new=_fake_threadpool):
        result = await uc.execute(
            principal=PRINCIPAL,
            messages=[(PROP_ID_1, REQ1), (PROP_ID_2, REQ2)],
        )

    assert len(result.predictions) == 2
    assert result.failed == []
    uow.rollback.assert_awaited_once()
    assert uow.begin_nested.await_count == 2
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_row_by_row_partial_failure():
    uc, uow, _ = make_uc(prices=(500.0, 600.0))
    uow.prediction.batch_add.side_effect = Exception("bulk fail")
    uow.prediction.add.side_effect = [None, Exception("row fail")]

    with patch("app.services.prediction.use_cases.batch.run_in_threadpool", new=_fake_threadpool):
        result = await uc.execute(
            principal=PRINCIPAL,
            messages=[(PROP_ID_1, REQ1), (PROP_ID_2, REQ2)],
        )

    assert len(result.predictions) == 1
    assert len(result.failed) == 1
    assert result.failed[0][0] == PROP_ID_2
    uow.rollback_to_savepoint.assert_awaited_once()
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_all_rows_fail_no_commit():
    uc, uow, _ = make_uc()
    uow.prediction.batch_add.side_effect = Exception("bulk fail")
    uow.prediction.add.side_effect = Exception("row fail")

    with patch("app.services.prediction.use_cases.batch.run_in_threadpool", new=_fake_threadpool):
        result = await uc.execute(
            principal=PRINCIPAL,
            messages=[(PROP_ID_1, REQ1), (PROP_ID_2, REQ2)],
        )

    assert result.predictions == []
    assert len(result.failed) == 2
    uow.rollback.assert_awaited_once()
    assert uow.rollback_to_savepoint.await_count == 2
    uow.commit.assert_not_awaited()
