---
title: Analytics Worker — wiring fixes, property_id mapping, MAXPOLL
captured-from: conversation
captured-on: 2026-05-25
participants: [raul, claude]
---

## Context
Final wiring session for the analytics-ms Kafka batch worker. Covered runtime fixes discovered during end-to-end testing.

## Key conclusions
- `PYTHONPATH=src` is required to run the worker locally (`PYTHONPATH=src uv run python src/app/workers/listing_created/runner.py`). Added `ENV PYTHONPATH=/app/src` to the Dockerfile — fixes both API and worker containers.
- `WorkerMessage.id` IS the `property_id`. After validation, set `message.model.property_id = message.id` in the consumer before inserting into `valid_messages`. Idempotent on retries.
- Kafka output topic `price-predicted` was serializing each prediction as a JSON array (tuple). Fixed to `{"property_id": uuid, "predicted_price": float}`.
- `max.poll.interval.ms` must be set to `1200000` (20 min) — default 300s is exceeded by the 900s sleep between poll cycles, causing Kafka to remove the consumer from the group.
- Runner logs: `setup_logging()` called only in `__main__` guard. Lifecycle events: `worker_init_start/done`, `worker_run_start`, `worker_batch_cycle_start/done`, `worker_fatal_error`.
- Retry flow is correct: `message.model.property_id` is already populated on retries (serialized in `model_dump()`), re-assignment on re-consume is idempotent.
- Unknown `barrio_ideca` at inference time: LightGBM treats it as NaN, follows NaN split branch — no crash, slight accuracy loss. Acceptable because `barrio_ideca` is always resolved by properties-service via IDECA catalog lookup before publishing to Kafka.

## Open questions
- None — analytics-ms considered MVP-complete for batch + online predict.

## Next steps
- Verify online predict router is wired and CORS is enabled before connecting the front-end.
- Front-end integration: call `/predict` for price estimate on listing creation form.
