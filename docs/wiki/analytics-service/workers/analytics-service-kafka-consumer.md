---
title: Kafka consumer — listing-created (analytics-service)
status: stable
last-verified: 2026-05-25
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[analytics-service-prediction]]
sources:
  - ../../../sources/analytics-service/2026-05-20-kafka-consumer-design.md
  - ../../../sources/analytics-service/2026-05-22-listing-consumer-worker-design.md
  - ../../../sources/analytics-service/2026-05-23-worker-runner-kafka-idempotency.md
  - ../../../sources/analytics-service/2026-05-25-worker-wiring-fixes.md
---

## TL;DR

Worker que consume el topic `listing-created`, valida mensajes con schema + circuit breaker de attempts, llama a `BatchPrediction.execute`, y produce a tres topics: predicciones, retry (mismo topic inicial), y DLQ. Proceso separado long-running sobre confluent-kafka con commit manual de offset.

## Estructura

```
workers/
└── listing_created/
    ├── consumer.py        # ListingConsumer
    ├── runner.py          # ListingWorkerRunner + build_consumer factory
    └── helpers/
        └── types.py       # WorkerMessage (Pydantic StrictBase)
```

## `WorkerMessage`

Pydantic `StrictBase` en `helpers/types.py`. Es el schema del envelope Kafka — valida el mensaje completo antes de pasarlo al UC:

```python
class WorkerMessage(StrictBase):
    id: uuid.UUID
    attempts: int = Field(default=1, ge=1, strict=True)
    model: PredictionRequest
```

`WorkerMessage.model_validate(data)` reemplaza la validación manual anterior (no hay `WorkerEnvelope` separado en consumer.py).

## `ListingConsumer`

```python
class ListingConsumer:
    def __init__(self, uc: BatchPrediction) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) / __exit__(self, *_): ...   # context manager
    def _poll_batch(self) -> tuple[list[str], list[str]]: ...  # (mensajes, rejected)
    async def consume_batch(self) -> None: ...

    @staticmethod def delivery_report(err, msg) -> None: ...
    @staticmethod def serialize(messages: list) -> list[str]: ...
    @staticmethod def produce(producer, topic, messages, callback) -> None: ...
```

### Mensaje de entrada

```json
{ "id": "uuid", "attempts": 1, "model": { ...PredictionRequest fields... } }
```

`WorkerMessage.id` ES el `property_id` del listing. Tras validar el mensaje, el consumer setea `message.model.property_id = message.id` antes de insertar en `valid_messages`. La operación es idempotente en retries porque el campo ya viene poblado en el model serializado.

`attempts` se incluye para el circuit breaker — lo incrementa el consumer al re-encolar.

### Flujo de `consume_batch`

1. **`_poll_batch()`** — devuelve `(messages, rejected_messages)`. Drena el topic con `poll(1.0)` hasta `msg is None`. `msg.error()` → log + continue. `UnicodeDecodeError` → serializa el raw como JSON base64 con `topic/partition/offset` y lo agrega a `rejected_messages`.
2. Si no hay mensajes ni rechazados → return temprano sin llamar al UC.
3. `rejected_messages` se extienden directamente al `dlq` (ya son strings JSON).
4. **Validación por mensaje**: `json.loads` → `WorkerMessage.model_validate(data)`. Si falla `JSONDecodeError` o `ValidationError` → DLQ. Luego `attempts > 3` → DLQ.
5. `message.model.property_id = message.id` — mapeo del property_id desde el envelope.
6. **`valid_messages: dict[UUID, WorkerMessage]`** — almacena el objeto `WorkerMessage` completo; acceso por atributo (`.id`, `.model`, `.attempts`).
6. Si solo hay DLQ y no `domain_messages` → publica DLQ, commitea y retorna.
7. **`BatchPrediction.execute`** recibe `list[tuple[UUID, PredictionRequest]]` extraída de `valid_messages`.
8. **Produces** vía `partial(_emit)`:
   - `topic_predictions` ← `serialize([{"property_id": uuid, "predicted_price": float} for ...])`
   - `topic` (mismo de entrada) ← `serialize(retry_messages)` con `attempts + 1` — solo si `result.failed`
   - `topic_dlq` ← `dlq` — solo si hubo malformados/rechazados
9. **`self.consumer.commit()`** — commit manual al final del batch.

### `produce` y `WorkerDeliveryError`

`produce()` colecta errores de delivery vía callback interno y verifica `flush()` pending. Si cualquiera falla lanza `WorkerDeliveryError(topic, errors, pending)`, lo que bloquea el `commit()` y garantiza re-proceso en el próximo ciclo.

## `ListingWorkerRunner`

Proceso long-running en `runner.py`. Orquesta el DI manual (sin FastAPI `Depends`) y el loop:

```python
class ListingWorkerRunner:
    def __init__(self) -> None:
        model_client = ModelClient()              # singleton — carga modelo al startup
        self.model = AVMModelAdapter(client=model_client)

    async def run(self) -> None:
        with Session(engine) as session:          # sesión vive todo el ciclo del worker
            uow = SqlPredictionUnitOfWork(session=session)
            uc = BatchPrediction(uow=uow, model=self.model)
            kafka_consumer = ListingConsumer(uc=uc)

            with kafka_consumer:                  # garantiza close() al salir
                while True:
                    await kafka_consumer.consume_batch()
                    await asyncio.sleep(900)      # batch cada 15 min
```

Arranque: `asyncio.run(ListingWorkerRunner().run())` — en CMD separado del Dockerfile (misma imagen, distinto entrypoint que uvicorn).

### `serialize`

```python
@staticmethod
def serialize(messages: list) -> list[str]:
    # json.dumps con default que maneja uuid.UUID → str y Pydantic → model_dump()
```

Usado para predictions (lista de dicts `{"property_id", "predicted_price"}`) y `retry_messages` (`list[dict]`). DLQ **no** pasa por serialize — ya son strings raw del poll.

### Context manager y cierre limpio

`close()` llama `self.consumer.close()` — hace commit del offset actual, unsubscribe del topic y libera la conexión. Sin esto el grupo queda en rebalancing hasta que expira el session timeout.

## Decisiones de diseño

### confluent-kafka sobre aiokafka
confluent-kafka es más production-grade (librdkafka bajo el capó). Llamadas bloqueantes (poll, flush) son síncronas pero están contenidas en métodos que se llaman desde el loop async del runner.

### `enable.auto.commit: False` + commit manual
El offset solo se commitea si el batch completo procesó (predictions emitidas, retries re-encolados, DLQ publicado). Garantiza at-least-once: si el proceso muere a mitad de batch, el próximo arranque re-procesa desde el último offset commiteado.

### `max.poll.interval.ms: 1200000`
El worker duerme 900s entre ciclos. El default de Kafka (300000ms = 5 min) es menor que ese intervalo — sin este override, Kafka saca al consumer del grupo al segundo ciclo y el siguiente `poll()` devuelve un error de rebalanceo. 1200000ms (20 min) da margen suficiente.

### Circuit breaker de attempts
`attempts > 3` → DLQ directo sin pasar al UC. Evita que mensajes problemáticos llenen el topic de retry indefinidamente.

### Topic de retry = topic inicial
Los mensajes fallidos del UC se re-encolan al mismo `KAFKA_TOPIC` (listing-created) con `attempts + 1`. No hace falta un topic de retry separado — el mismo consumer los recogerá en el próximo batch con el contador actualizado.

### Proceso separado, no APScheduler dentro de FastAPI
`ModelClient` carga el modelo en `ListingWorkerRunner.__init__` — un cron que reinicia el proceso cada ciclo recargaría el modelo (caro). El proceso long-running mantiene el modelo en memoria entre ciclos.

### Logs del runner
`setup_logging()` se llama solo en el guard `if __name__ == "__main__"` — no configura el logging global cuando se importa como módulo. Eventos de ciclo de vida: `worker_init_start`, `worker_init_done`, `worker_run_start`, `worker_batch_cycle_start`, `worker_batch_cycle_done`, `worker_fatal_error` (con `exc_info`).

### Idempotencia — sin constraint único para MVP
Múltiples predicciones por `property_id` son datos válidos de negocio (evolución del precio estimado). `on_conflict_do_nothing()` en `batch_add` actúa como red de seguridad para redeliveries manuales. Kafka at-least-once duplicados son raros a escala MVP. Decisión revisable cuando haya DWH con SCD2.

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

## Claims

- Clase se llama `ListingConsumer` (no `ListingCreatedConsumer`) ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `enable.auto.commit: False` configurado en el consumer — offset se commitea manualmente al final de `consume_batch` ([consumer.py:41](backend/analytics-service/src/app/workers/listing_created/consumer.py#L41)).
- `max.poll.interval.ms: 1200000` configurado en el consumer — necesario porque el worker duerme 900s entre ciclos, superando el default de 300s ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `WorkerMessage` es un Pydantic `StrictBase` con campos `id: UUID`, `attempts: int = Field(ge=1, strict=True)`, `model: PredictionRequest` ([helpers/types.py](backend/analytics-service/src/app/workers/listing_created/helpers/types.py)).
- `WorkerMessage.id` es el `property_id` del listing — el consumer setea `message.model.property_id = message.id` tras validar cada mensaje ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- No hay `WorkerEnvelope` en consumer.py — `WorkerMessage.model_validate(data)` valida el envelope completo.
- `_poll_batch()` devuelve `tuple[list[str], list[str]]` — decode failures van como JSON base64 en la segunda lista ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `produce()` lanza `WorkerDeliveryError` si el callback reporta errores o `flush()` deja mensajes pendientes — bloquea el commit de offsets.
- `WorkerConfigurationError` hereda `BaseError` y recibe `missing: list[str]` ([core/exceptions/worker.py](backend/analytics-service/src/app/core/exceptions/worker.py)).
- Topic `price-predicted` recibe mensajes con shape `{"property_id": uuid, "predicted_price": float}` — no tuplas ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- Topic de retry es el mismo `KAFKA_TOPIC` — no hay env var separada para retry.
- DLQ no pasa por `serialize` — son strings JSON ya formateados.
- Context manager implementado: `__exit__` llama `self.consumer.close()` ([consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `ListingWorkerRunner.__init__` crea `ModelClient` y `AVMModelAdapter` como singletons; `Session(engine)` se abre dentro de `run()` para que viva todo el ciclo ([runner.py](backend/analytics-service/src/app/workers/listing_created/runner.py)).
- El loop duerme `asyncio.sleep(900)` entre ciclos — batch cada 15 minutos.
- `setup_logging()` se invoca solo en el guard `__main__` del runner — no afecta imports del módulo ([runner.py](backend/analytics-service/src/app/workers/listing_created/runner.py)).
