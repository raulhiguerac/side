---
title: Worker Runner Architecture & Kafka Idempotency Decision
captured-from: conversation
captured-on: 2026-05-23
participants: [raul, claude]
---

## Context
Implementing the Kafka worker entrypoint for analytics-service. The worker consumes `listing_created` events, runs batch predictions via the AVM model, and publishes results back to Kafka. Discussion covered manual DI wiring, consumer loop design, and idempotency strategy.

## Key conclusions

### Worker Runner (`ListingWorkerRunner`)
- `ModelClient` and `AVMModelAdapter` are singletons — instantiated in `__init__`, outside the session scope.
- `Session(engine)` lives inside `run()` so it stays open for the full worker lifecycle (not just during build).
- Chain built manually (no FastAPI `Depends`): `Session → SqlPredictionUnitOfWork → BatchPrediction → ListingConsumer`.
- Loop: `while True: await consume_batch() → asyncio.sleep(900)` — batch processing every 15 min.
- `ListingConsumer` used as context manager (`with kafka_consumer`) to guarantee `consumer.close()` on exit.
- Entry: separate script calls `asyncio.run(ListingWorkerRunner().run())` — same Docker image, different CMD.

### Consumer refactor
- `WorkerMessage` in `helpers/types.py` promoted from `TypedDict` to Pydantic model (`StrictBase`) with field validation (`attempts: int = Field(ge=1, strict=True)`).
- `WorkerEnvelope` removed from `consumer.py` — `WorkerMessage.model_validate()` replaces it.
- `valid_messages: dict[uuid.UUID, WorkerMessage]` stores envelope objects; access via attributes, not dict keys.
- `_poll_batch()` returns `(messages, rejected_messages)` — UTF-8 decode failures serialized as base64 JSON with topic/partition/offset metadata and sent to DLQ.
- `produce()` collects delivery errors via callback + checks `flush()` pending count; raises `WorkerDeliveryError` if either fails, blocking offset commit.

### Idempotency — no constraint for MVP
- Decision: **no unique constraint on `predictions.property_id`** for now.
- Rationale: multiple predictions per listing is valid business data (price evolution over time). `created_at` already captures history for free.
- At-least-once Kafka duplicates are rare and acceptable at MVP scale.
- `on_conflict_do_nothing()` in `batch_add` remains as a safety net for manual redeliveries.
- Future path: partial unique index on `(property_id, created_at)` or SCD2 in DWH if strict deduplication is needed.

## Open questions
- `WORKER_PRINCIPAL` env var is read as `str` but `BatchPrediction.execute` expects `uuid.UUID` — passes `None` (Optional) if unset, but a non-None string would fail at DB insert. Needs cast or explicit nullable handling.

## Next steps
- Add `asyncio.run` entrypoint script (or Dockerfile CMD) to boot the runner.
- Alembic migration for `predictions` table — still missing `alembic.ini` + `env.py`.
