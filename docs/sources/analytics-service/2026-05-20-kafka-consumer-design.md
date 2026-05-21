---
title: Diseño del Kafka consumer — listing-created → BatchPrediction
captured-from: conversation
captured-on: 2026-05-20
participants: [author, claude]
---

## Context

Sesión de diseño del worker que consume el topic `listing-created` y llama al UC `BatchPrediction.execute`. El UC ya estaba implementado; faltaba decidir la arquitectura del consumer y arrancar el código.

## Key conclusions

- **confluent-kafka** elegido sobre aiokafka — más production-grade; operaciones bloqueantes se envuelven con `run_in_threadpool` igual que el resto del servicio.
- **Cadencia de 15 minutos** — no polling estricto sino micro-batch: el consumer drena el topic, procesa, publica, duerme 900s.
- **Proceso separado long-running** (no APScheduler dentro de FastAPI, no cron) — mantiene el `ModelClient` con el modelo en memoria entre corridas; ciclo de vida independiente del web server.
- **Estructura**: `workers/listing_created/consumer.py` + `workers/listing_created/main.py`. La clase `ListingCreatedConsumer` solo expone `consume_batch()` — el loop y el sleep viven en `main.py`.
- **DLQ sí, pero acotado**: `listing-created-dlq` solo para errores de deserialización/validación (mensajes irrecuperables). Fallos de modelo ya tienen camino propio — el UC devuelve `failed` y el consumer los re-encola a `listing-created`.
- **`group.id`** es obligatorio en confluent-kafka. Con múltiples pods y mismo `group.id`, Kafka distribuye particiones entre instancias — el paralelismo real está limitado por el número de particiones del topic.

## Bugs encontrados en el stub inicial

- `os.getenv` nunca lanza excepción — `try/except` alrededor es inútil; validación debe ser explícita (`if not server: raise`).
- `|` (bitwise OR) usado para validar strings en vez de `or`.
- Nombre de clase `Consumer` colisiona con `from confluent_kafka import Consumer`.
- `consumer.poll()` devuelve un solo mensaje, no lista — para drenar usar loop con `poll(timeout)` o `consume(num_messages, timeout)`.
- `break` fuera del `if msg` causaba que el loop siempre hiciera exactamente una iteración.
- Deserialización pendiente: `PredictionRequest.model_validate_json(value)` para armar las tuplas `(UUID, PredictionRequest)`.

## Open questions

- Número de particiones para `listing-created` (define el paralelismo máximo).
- Mecanismo de mensajería definitivo aún pendiente de confirmar (Kafka asumido pero no decidido formalmente).

## Next steps

- Corregir el loop de poll y manejar `msg.error()`.
- Deserializar con `PredictionRequest.model_validate_json` y armar `list[tuple[UUID, PredictionRequest]]`.
- Llamar `self.uc.execute` y publicar resultados al producer.
- Implementar `main.py` con `while True: consume_batch(); sleep(900)`.
- Decidir e implementar el producer (publica a `price-predicted`, re-encola fallidos a `listing-created`, DLQ para irrecuperables).
