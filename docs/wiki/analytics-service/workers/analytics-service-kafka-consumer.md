---
title: Kafka consumer — listing-created (analytics-service)
status: draft
last-verified: 2026-05-20
owners: [analytics-service]
related: [[analytics-service]], [[analytics-service-architecture]], [[analytics-service-prediction]]
sources: [../../../sources/analytics-service/2026-05-20-kafka-consumer-design.md]
---

## TL;DR

Worker que consume el topic `listing-created`, llama a `BatchPrediction.execute` en micro-batches de 15 minutos, publica predicciones a `price-predicted` y re-encola fallidos. Proceso separado long-running sobre confluent-kafka.

## Estructura

```
workers/
└── listing_created/
    ├── consumer.py   # ListingCreatedConsumer — consume_batch()
    └── main.py       # entrypoint — loop + sleep(900)
```

## `ListingCreatedConsumer`

```python
class ListingCreatedConsumer:
    def __init__(self, uc: BatchPrediction, producer: ..., settings: ...): ...
    def consume_batch(self) -> None: ...
```

Dependencias inyectadas al construir — no instancia nada internamente. `main.py` resuelve las dependencias y llama `consume_batch()` en un loop.

### Flujo de `consume_batch`

1. Drena el topic `listing-created` con `poll(timeout)` o `consume(num_messages, timeout)` hasta que no haya más mensajes.
2. Por cada mensaje: `msg.error()` primero — si tiene error Kafka, va a DLQ. Si no, `PredictionRequest.model_validate_json(msg.value().decode())` — si falla deserialización/validación, va a DLQ.
3. Arma `list[tuple[UUID, PredictionRequest]]` con los mensajes válidos.
4. Llama `BatchPrediction.execute(principal=SYSTEM_PRINCIPAL_ID, messages=batch)` vía `run_in_threadpool`.
5. Publica `result.predictions` → topic `price-predicted`.
6. Re-encola `result.failed` → topic `listing-created` (Kafka at-least-once ya protegido por `ON CONFLICT DO NOTHING` en `batch_add`).

### `main.py`

```python
while True:
    consumer.consume_batch()
    sleep(900)
```

## Decisiones de diseño

### confluent-kafka sobre aiokafka
confluent-kafka es más production-grade (librdkafka bajo el capó). Las llamadas bloqueantes se envuelven con `run_in_threadpool` — patrón ya establecido en el servicio para MLflow y SQLAlchemy.

### Proceso separado, no APScheduler dentro de FastAPI
- `ModelClient` carga el modelo al `__init__` — un cron que reinicia el proceso cada 15 min recargaría el modelo en cada run (caro).
- Un proceso long-running mantiene el modelo en memoria entre corridas.
- Ciclo de vida independiente del web server: se puede reiniciar/escalar sin afectar `/predict`.

### Cadencia de 15 minutos
El enriquecimiento de `estimated_price` en listings no requiere latencia sub-segundo — 15 min es suficiente para la UX del producto. Simplifica el diseño vs polling continuo.

### DLQ acotado
`listing-created-dlq` solo para mensajes irrecuperables (deserialización fallida, schema inválido). Fallos de modelo ya tienen su ruta: el UC devuelve `BatchPredictionResult.failed` y el consumer los re-encola a `listing-created` para reintentar en el próximo batch.

### `group.id` y escalado

`group.id = "analytics-listing-consumer"` es fijo e igual en todos los pods. Kafka distribuye las particiones del topic entre las instancias del grupo — con N pods y M particiones, cada pod lee ≤ M/N particiones. El paralelismo real está limitado por el número de particiones de `listing-created`.

## Env vars requeridas

| Var | Ejemplo |
|---|---|
| `KAFKA_SERVER` | `kafka:9092` |
| `KAFKA_GROUP_ID` | `analytics-listing-consumer` |
| `KAFKA_TOPIC` | `listing-created` |

## Estado al 2026-05-20

`consumer.py` existe con la estructura de clase y el `__init__` correcto. `consume_batch()` está en construcción — falta: loop de poll corregido, manejo de `msg.error()`, deserialización con `model_validate_json`, llamada al UC, producer.

## Claims

- `ListingCreatedConsumer.__init__` recibe `uc: BatchPrediction` como dependencia inyectada — no instancia el UC internamente ([workers/listing_created/consumer.py](backend/analytics-service/src/app/workers/listing_created/consumer.py)).
- `KAFKA_SERVER`, `KAFKA_GROUP_ID` y `KAFKA_TOPIC` se leen de env vars — fallar explícitamente si alguna falta.
- `group.id` es obligatorio en confluent-kafka — sin él falla al instanciar el consumer antes de hacer poll.
- El DLQ es `listing-created-dlq` solo para errores de deserialización; fallos de modelo van de vuelta a `listing-created` vía `BatchPredictionResult.failed`.
- El proceso separado mantiene el modelo MLflow en memoria entre corridas — un cron recargaría el modelo en cada ejecución.
