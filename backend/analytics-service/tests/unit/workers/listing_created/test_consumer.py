import base64
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions.worker import WorkerConfigurationError, WorkerDeliveryError
from app.models.prediction import PropertyType
from app.services.prediction.schemas.prediction import BatchPredictionResult, PredictionRequest
from app.workers.listing_created.consumer import ListingConsumer

from .conftest import (
    PRINCIPAL,
    PROP_ID,
    VALID_MODEL_DICT,
    VALID_MSG,
    _ENV,
    bad_utf8_msg,
    error_msg,
    good_msg,
    make_consumer,
    poll_seq,
)


def _make_result(*, predictions=(), failed=()):
    return BatchPredictionResult(predictions=list(predictions), failed=list(failed))


def _make_req(**overrides):
    data = {**VALID_MODEL_DICT, "property_id": PROP_ID, **overrides}
    return PredictionRequest(**data)


# ── Configuration ──────────────────────────────────────────────────────────────


class TestConfiguration:
    def test_missing_env_vars_raise(self, monkeypatch):
        for k in _ENV:
            monkeypatch.delenv(k, raising=False)
        with (
            patch("app.workers.listing_created.consumer.Consumer"),
            patch("app.workers.listing_created.consumer.Producer"),
            pytest.raises(WorkerConfigurationError),
        ):
            ListingConsumer(uc=AsyncMock())

    def test_invalid_principal_uuid_raises(self, monkeypatch):
        for k, v in _ENV.items():
            monkeypatch.setenv(k, v)
        monkeypatch.setenv("WORKER_PRINCIPAL", "not-a-uuid")
        with (
            patch("app.workers.listing_created.consumer.Consumer"),
            patch("app.workers.listing_created.consumer.Producer"),
            pytest.raises(WorkerConfigurationError),
        ):
            ListingConsumer(uc=AsyncMock())

    def test_principal_stored_as_uuid(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        assert c.principal == PRINCIPAL
        assert isinstance(c.principal, uuid.UUID)

    def test_topic_attrs_set_from_env(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        assert c.topic == "listing-created"
        assert c.topic_predictions == "price-predicted"
        assert c.topic_dlq == "listing-created-dlq"

    def test_context_manager_calls_close(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        with c:
            pass
        c.consumer.close.assert_called_once()


# ── _poll_batch ────────────────────────────────────────────────────────────────


class TestPollBatch:
    def test_none_poll_returns_empty_lists(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c)
        raw, rejected = c._poll_batch()
        assert raw == [] and rejected == []

    def test_error_message_is_skipped(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c, error_msg())
        raw, rejected = c._poll_batch()
        assert raw == [] and rejected == []

    def test_valid_message_decoded(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c, good_msg(VALID_MSG))
        raw, rejected = c._poll_batch()
        assert raw == [VALID_MSG] and rejected == []

    def test_multiple_messages_collected(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c, good_msg(VALID_MSG), good_msg(VALID_MSG))
        raw, rejected = c._poll_batch()
        assert len(raw) == 2

    def test_bad_utf8_goes_to_rejected_with_base64(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c, bad_utf8_msg())
        raw, rejected = c._poll_batch()
        assert raw == [] and len(rejected) == 1
        parsed = json.loads(rejected[0])
        assert parsed["reason"] == "MESSAGE_DECODE_FAILED"
        assert parsed["encoding"] == "base64"
        assert base64.b64decode(parsed["value"]) == b"\xff\xfe"

    def test_mixed_messages_split_correctly(self, monkeypatch):
        c, _ = make_consumer(monkeypatch)
        poll_seq(c, good_msg(VALID_MSG), bad_utf8_msg())
        raw, rejected = c._poll_batch()
        assert len(raw) == 1 and len(rejected) == 1


# ── produce() ─────────────────────────────────────────────────────────────────


class TestProduce:
    def test_no_error_does_not_raise(self):
        producer = MagicMock()
        producer.flush.return_value = 0
        ListingConsumer.produce(producer, "topic", ["msg"], lambda e, m: None)

    def test_flush_pending_raises_delivery_error(self):
        producer = MagicMock()
        producer.flush.return_value = 2
        with pytest.raises(WorkerDeliveryError):
            ListingConsumer.produce(producer, "topic", ["msg"], lambda e, m: None)

    def test_delivery_callback_error_raises_delivery_error(self):
        producer = MagicMock()
        producer.flush.return_value = 0

        def _trigger_error(topic, value=None, on_delivery=None):
            on_delivery("delivery failed", MagicMock())

        producer.produce.side_effect = _trigger_error
        with pytest.raises(WorkerDeliveryError):
            ListingConsumer.produce(producer, "topic", ["msg"], lambda e, m: None)

    def test_message_encoded_as_utf8(self):
        producer = MagicMock()
        producer.flush.return_value = 0
        ListingConsumer.produce(producer, "topic", ['{"a": 1}'], lambda e, m: None)
        _, call_kwargs = producer.produce.call_args
        assert call_kwargs["value"] == b'{"a": 1}'


# ── serialize() ───────────────────────────────────────────────────────────────


class TestSerialize:
    def test_uuid_value_becomes_str(self):
        uid = uuid.uuid4()
        [result] = ListingConsumer.serialize([{"id": uid}])
        assert json.loads(result)["id"] == str(uid)

    def test_pydantic_model_uses_model_dump(self):
        model = MagicMock()
        model.model_dump.return_value = {"key": "val"}
        [result] = ListingConsumer.serialize([{"nested": model}])
        assert json.loads(result)["nested"] == {"key": "val"}

    def test_non_serializable_raises_type_error(self):
        with pytest.raises(TypeError):
            ListingConsumer.serialize([{"bad": object()}])

    def test_returns_one_json_string_per_message(self):
        results = ListingConsumer.serialize([{"a": 1}, {"b": 2}])
        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)


# ── consume_batch ──────────────────────────────────────────────────────────────


class TestConsumeBatch:
    @pytest.mark.asyncio
    async def test_empty_poll_returns_early_no_uc_call(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        with patch.object(c, "_poll_batch", return_value=([], [])):
            await c.consume_batch()
        uc.execute.assert_not_awaited()
        c.consumer.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_only_emits_dlq_and_commits(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        rejected = ['{"reason": "MESSAGE_DECODE_FAILED"}']
        with (
            patch.object(c, "_poll_batch", return_value=([], rejected)),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        uc.execute.assert_not_awaited()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "listing-created-dlq" in topics
        c.consumer.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_json_goes_to_dlq(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        with (
            patch.object(c, "_poll_batch", return_value=(["not-json"], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        uc.execute.assert_not_awaited()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "listing-created-dlq" in topics

    @pytest.mark.asyncio
    async def test_validation_error_goes_to_dlq(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        bad = json.dumps({"id": str(PROP_ID), "attempts": 1, "model": {"area_m2": -1}})
        with (
            patch.object(c, "_poll_batch", return_value=([bad], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        uc.execute.assert_not_awaited()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "listing-created-dlq" in topics

    @pytest.mark.asyncio
    async def test_attempts_above_3_goes_to_dlq(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        msg = json.dumps({"id": str(PROP_ID), "attempts": 4, "model": VALID_MODEL_DICT})
        with (
            patch.object(c, "_poll_batch", return_value=([msg], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        uc.execute.assert_not_awaited()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "listing-created-dlq" in topics

    @pytest.mark.asyncio
    async def test_valid_message_calls_uc_with_correct_principal(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500.0)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])),
            patch.object(c, "produce"),
        ):
            await c.consume_batch()
        uc.execute.assert_awaited_once()
        assert uc.execute.call_args[1]["principal"] == PRINCIPAL

    @pytest.mark.asyncio
    async def test_property_id_set_from_envelope_id(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500.0)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])),
            patch.object(c, "produce"),
        ):
            await c.consume_batch()
        _, req = uc.execute.call_args[1]["messages"][0]
        assert req.property_id == PROP_ID

    @pytest.mark.asyncio
    async def test_predictions_published_as_dict_with_correct_fields(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500_000.0)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        pred_call = next(
            (cl for cl in mock_produce.call_args_list if cl[1]["topic"] == "price-predicted"),
            None,
        )
        assert pred_call is not None
        [payload_str] = pred_call[1]["messages"]
        payload = json.loads(payload_str)
        assert payload["property_id"] == str(PROP_ID)
        assert payload["predicted_price"] == 500_000.0

    @pytest.mark.asyncio
    async def test_failed_messages_retried_with_incremented_attempts(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        msg_attempts_2 = json.dumps({"id": str(PROP_ID), "attempts": 2, "model": VALID_MODEL_DICT})
        req = _make_req()
        uc.execute.return_value = _make_result(failed=[(PROP_ID, req)])
        with (
            patch.object(c, "_poll_batch", return_value=([msg_attempts_2], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        retry_call = next(
            (cl for cl in mock_produce.call_args_list if cl[1]["topic"] == "listing-created"),
            None,
        )
        assert retry_call is not None
        [retry_str] = retry_call[1]["messages"]
        retry = json.loads(retry_str)
        assert retry["attempts"] == 3

    @pytest.mark.asyncio
    async def test_no_predictions_topic_when_all_fail(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        req = _make_req()
        uc.execute.return_value = _make_result(failed=[(PROP_ID, req)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "price-predicted" not in topics

    @pytest.mark.asyncio
    async def test_commit_called_after_successful_batch(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500.0)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG], [])),
            patch.object(c, "produce"),
        ):
            await c.consume_batch()
        c.consumer.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mixed_dlq_and_valid_both_emitted(self, monkeypatch):
        c, uc = make_consumer(monkeypatch)
        bad = "not-json"
        uc.execute.return_value = _make_result(predictions=[(PROP_ID, 500.0)])
        with (
            patch.object(c, "_poll_batch", return_value=([VALID_MSG, bad], [])),
            patch.object(c, "produce") as mock_produce,
        ):
            await c.consume_batch()
        topics = [cl[1]["topic"] for cl in mock_produce.call_args_list]
        assert "price-predicted" in topics
        assert "listing-created-dlq" in topics
