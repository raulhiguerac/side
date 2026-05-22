---
title: ListingConsumer — diseño e implementación del worker Kafka
captured-from: conversation
captured-on: 2026-05-22
participants: [raul, claude]
---

## Context

Se diseñó e implementó `ListingConsumer`, el worker Kafka del `analytics-service` que consume el topic `listing_created`, valida mensajes, invoca `BatchPrediction`, y produce resultados a tres topics de salida (predictions, retry, DLQ).

## Key conclusions

- **Mensaje de entrada**: wrapper `{ "id": uuid, "attempts": int, "model": PredictionRequest }` — `json.loads` sobre el wrapper, `model_validate` solo sobre `data["model"]`.
- **`valid_messages` como `dict[UUID, WorkerMessage]`**: keyed por UUID para O(1) lookup al construir retries; evita listas paralelas.
- **Circuit breaker de attempts**: `attempts > 3` → DLQ directo, sin pasar al UC.
- **Tres topics de salida**: `KAFKA_PREDICTIONS_TOPIC` (éxitos), `KAFKA_TOPIC` (retry con attempts+1), `KAFKA_DLQ_TOPIC` (malformados e irrecuperables). El topic de retry es el mismo topic inicial — no hace falta `KAFKA_RETRY_TOPIC`.
- **`enable.auto.commit: False`** + `self.consumer.commit()` al final de `consume_batch` — semántica at-least-once; el offset solo se commitea si el batch completo procesó.
- **`serialize` como `@staticmethod`** con `json.dumps(default=_default)`: maneja `uuid.UUID` → `str` y Pydantic models → `model_dump()` automáticamente. DLQ pasa directo (ya son strings).
- **`partial(_emit)`** vincula `producer` y `callback` una sola vez — los tres produces quedan en 3 líneas.
- **Context manager** (`__enter__`/`__exit__` → `close()`): `consumer.close()` hace commit de offset, unsubscribe y libera conexión. Sin esto el grupo queda en rebalancing al apagarse.
- **`WorkerMessage` TypedDict** en `helpers/types.py` (renombrado desde `helpers/consumer.py`): campos `id: UUID`, `attempts: int`, `request: PredictionRequest`.
- **`WorkerConfigurationError`** en `core/exceptions/worker.py` — hereda `BaseError`, recibe `missing: list[str]` de env vars faltantes.
- **`_poll_batch()`** extraído como método privado: `if msg is None: break`, `if msg.error(): continue` (manejo explícito de errores de Kafka), `UnicodeDecodeError` logueado sin romper el loop.

## Open questions

- Entry point del worker (`main.py`) no existe todavía — falta la factory/DI que construye `BatchPrediction` y el loop `while True: await consumer.consume_batch()`.

## Next steps

- Crear el entry point del worker con el `with ListingConsumer(uc=uc) as consumer` y el loop principal.
- Agregar `KAFKA_PREDICTIONS_TOPIC`, `KAFKA_DLQ_TOPIC` al `.env.example` del servicio.
