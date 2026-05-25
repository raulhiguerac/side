---
title: Analytics Service Unit Test Suite
captured-from: conversation
captured-on: 2026-05-25
participants: [raul, claude]
---

## Context
Wrote the complete unit test suite for analytics-service (63 tests across 6 files) covering the prediction domain, AVM adapter, and the Kafka worker consumer.

## Key conclusions
- `asyncio_mode = "auto"` in `pyproject.toml` — `@pytest.mark.asyncio` is optional but harmless.
- Tests run with `uv run python -m pytest tests/unit/` (pytest is under `[project.optional-dependencies] dev`; activate with `uv sync --extra dev`).
- `async def _fake_threadpool(func): return func()` — standard pattern to replace `run_in_threadpool` in UC tests; patches at the import path of the UC module (e.g. `app.services.prediction.use_cases.online.run_in_threadpool`).
- UoW repo methods are **sync** → `MagicMock`; async UoW methods (`commit`, `rollback`, etc.) → `AsyncMock`.
- `BatchPredictionResult` is a Pydantic model — instantiate it directly in tests rather than mocking, e.g. `BatchPredictionResult(predictions=[(PROP_ID, 500.0)], failed=[])`.
- Consumer fixture pattern: `make_consumer(monkeypatch)` factory in `conftest.py` — patches `Consumer` and `Producer` via context manager, then returns the already-created mock instances via `c.consumer` / `c.producer`; mock instances persist after the `with` block exits.
- `poll_seq(consumer, *msgs)` helper: sets `consumer.consumer.poll.side_effect = list(msgs) + [None]` — always append `None` or poll loop raises `StopIteration`.
- `patch.object(c, "produce")` works on static methods — adds an instance attribute that shadows the class attribute; `partial(self.produce, ...)` picks up the instance-level mock.
- Bad UTF-8 messages: use real bytes `b"\xff\xfe"` as `msg.value.return_value`; `.decode("utf-8")` raises `UnicodeDecodeError` naturally, and `base64.b64encode()` still works on the raw bytes.
- `consume_batch` tests patch `_poll_batch` directly via `patch.object(c, "_poll_batch", return_value=(...))` to avoid poll loop complexity; `_poll_batch` tests use real poll via `poll_seq`.

## Open questions
- None — suite is complete and all 63 tests pass.

## Next steps
- Integration tests (real DB + real Kafka) remain pending for post-MVP.
- Fix `uuid.UUID(raw)` validation error handling in `consumer.__init__` (already has try/except, was flagged and fixed in the same session).
- Fix `CORSMiddleware` to use explicit origins + `allow_credentials=True` before connecting the front-end.
