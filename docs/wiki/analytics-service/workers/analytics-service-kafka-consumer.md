---
title: Kafka consumer — listing-created (analytics-service)
status: draft
last-verified: 2026-05-22
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[analytics-service-prediction]]
sources:
  - ../../../sources/analytics-service/2026-05-20-kafka-consumer-design.md
  - ../../../sources/analytics-service/2026-05-22-listing-consumer-worker-design.md
---

## TL;DR

Worker que consume el topic `listing-created`, valida mensajes con schema + circuit breaker de attempts, llama a `BatchPrediction.execute`, y produce a tres topics: predicciones, retry (mismo topic inicial), y DLQ. Proceso separado long-running sobre confluent-kafka con commit manual de offset.

## Estructura

```
workers/
└── listing_created/
    ├── consumer.py        # ListingConsumer
    └── helpers/
        └── types.py       # WorkerMessage TypedDict
```

`main.py` (entry point + loop) está pendiente.

## `ListingConsumer`

```python
class ListingConsumer:
    def __init__(self, uc: BatchPrediction) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) / __exit__(self, *_): ...   # context manager
    def _poll_batch(self) -> list[str]: ...
    async def consume_batch(self) -> None: ...

    @staticmethod def delivery_report(err, msg) -> None: ...
    @staticmethod def serialize(messages: list) -> list[str]: ...
    @staticmethod def produce(producer, topic, messages, callback) -> None: ...
```

Uso con context manager:
```python
with ListingConsumer(uc=uc) as consumer:
    await consumer.consume_batch()
```

### Mensaje de entrada

```json
{ "id": "uuid", "attempts": 1, "model": { ...PredictionRequest fields... } }
```

`attempts` se incluye para el circuit breaker — lo incrementa el consumer al re-encolar.

### Flujo de `consume_batch`

1. **`_poll_batch()`** — drena el topic con `poll(1.0)` hasta `msg is None`. `msg.error()` → log + continue. `UnicodeDecodeError` → log + skip.
2. **Validación por mensaje**: `json.loads` → si falla `JSONDecodeError` → DLQ. Luego `attempts > 3` → DLQ. Luego `PredictionRequest.model_validate(data["model"])` + `uuid.UUID(data["id"])` → si falla `(ValidationError, KeyError, ValueError)` → DLQ.
3. **`valid_messages: dict[UUID, WorkerMessage]`** — keyed por UUID para O(1) lookup en el paso de retry.
4. **`BatchPrediction.execute`** recibe `list[tuple[UUID, PredictionRequest]]` extraída del dict.
5. **Produces** vía `partial(_emit)` con producer y callback vinculados una sola vez:
   - `topic_predictions` ← `serialize(result.predictions)`
   - `topic` (mismo de entrada) ← `serialize(retry_messages)` con `attempts + 1` — solo si `result.failed`
   - `topic_dlq` ← `dlq` directo (ya son strings) — solo si hubo malformados
6. **`self.consumer.commit()`** — commit manual al final del batch.

### `serialize`

```python
@staticmethod
def serialize(messages: list) -> list[str]:
    # json.dumps con default que maneja uuid.UUID → str y Pydantic → model_dump()
```

Usado para `result.predictions` (`list[tuple[UUID, float]]`) y `retry_messages` (`list[dict]`). DLQ **no** pasa por serialize — ya son strings raw del poll.

### Context manager y cierre limpio

`close()` llama `self.consumer.close()` — hace commit del offset actual, unsubscribe del topic y libera la conexión. Sin esto el grupo queda en rebalancing hasta que expira el session timeout.

## Decisiones de diseño

### confluent-kafka sobre aiokafka
confluent-kafka es más production-grade (librdkafka bajo el capó). Llamadas bloqueantes se envuelven con `run_in_threadpool` — patrón ya establecido en el servicio para MLflow y SQLAlchemy.

### `enable.auto.commit: False` + commit manual
El offset solo se commitea si el batch completo procesó (predictions emitidas, retries re-encolados, DLQ publicado). Garantiza at-least-once: si el proceso muere a mitad de batch, el próximo arranque re-procesa desde el último offset commiteado.

### Circuit breaker de attempts
`attempts > 3` → DLQ directo sin pasar al UC. Evita que mensajes problemáticos llenen el topic de retry indefinidamente.

### Topic de retry = topic inicial
Los mensajes fallidos del UC se re-encolan al mismo `KAFKA_TOPIC` (listing-created) con `attempts + 1`. No hace falta un topic de retry separado — el mismo consumer los recogerá en el próximo batch con el contador actualizado.

### Proceso separado, no APScheduler dentro de FastAPI
`ModelClient` carga el modelo al `__init__` — un cron que reinicia el proceso cada ciclo recargaría el modelo (caro). Un proceso long-running mantiene el modelo en memoria.

### `group.id` y escalado
`group.id = "analytics-listing-consumer"` fijo en todos los pods. Kafka distribuye particiones entre instancias del grupo — el paralelismo real está limitado por el número de particiones de `listing-created`.

## Env vars requeridas

| Var | Ejemplo |
|---|---|
| `KAFKA_SERVER` | `kafka:9092` |
| `KAFKA_GROUP_ID` | `analytics-listing-consumer` |
| `KAFKA_TOPIC` | `listing-created` |
| `KAFKA_PREDICTIONS_TOPIC` | `price-predicted` |
| `KAFKA_DLQ_TOPIC` | `listing-created-dlq` |
| `WORKER_PRINCIPAL` | UUID del principal de sistema |

`WorkerConfigurationError` se lanza al inicio si alguna de las primeras 5 falta.

## Estado al 2026-05-22

`consumer.py` implementado con poll, validación, UC call, tres produces y commit manual. `helpers/types.py` con `WorkerMessage`. `core/exceptions/worker.py` con `WorkerConfigurationError`. Pendiente: `main.py` (entry point + loop).

## Claims

- Clase se llama `ListingConsumer` (no `ListingCreatedConsumer`) ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `enable.auto.commit: False` configurado en el consumer — offset se commitea manualmente al final de `consume_batch` ([consumer.py:41](backend/analytics-service/src/app/workers/listing_created/consumer.py#L41)).
- `WorkerMessage` TypedDict tiene campos `id: UUID`, `attempts: int`, `request: PredictionRequest` ([helpers/types.py](backend/analytics-service/src/app/workers/listing_created/helpers/types.py)).
- `WorkerConfigurationError` hereda `BaseError` y recibe `missing: list[str]` ([core/exceptions/worker.py](backend/analytics-service/src/app/core/exceptions/worker.py)).
- Topic de retry es el mismo `KAFKA_TOPIC` — no hay env var separada para retry.
- DLQ no pasa por `serialize` — son strings raw del poll, se producen directamente.
- Context manager implementado: `__exit__` llama `self.consumer.close()` ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
