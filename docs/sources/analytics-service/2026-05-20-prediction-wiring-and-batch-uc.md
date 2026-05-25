---
title: Wiring de /predict y UC de batch — analytics-service
captured-from: conversation
captured-on: 2026-05-20
participants: [author, claude]
---

## Context

Sesión de implementación del wiring completo del endpoint `/predict` y el UC de batch para el flujo Kafka `listing-created → price-predicted`. El dominio `prediction` ya tenía ports/adapters/UC online, pero faltaba todo el glue: deps, route, DB, auth y el UC de batch.

## Key conclusions

### Estructura de deps
- `api/deps/__init__.py` vacío — cada responsabilidad en su propio archivo: `auth.py`, `db.py`, `prediction.py`.
- `@lru_cache(maxsize=1)` para `ModelClient` y `AVMModelAdapter` — son singletons stateless, se instancian una sola vez al primer request.
- Errores `UnauthorizedError` y `ForbiddenError` viven en `core/exceptions/auth.py`, **no** en `api/deps/auth.py`. Los otros MSs los definen en el archivo de deps — es una inconsistencia pre-existente que se corrigió aquí.

### run_in_threadpool
- Se aplica tanto a la inferencia del modelo (`online_predict`, `batch_predict`) como a las operaciones de repo (`add`, `batch_add`) — ambas son bloqueantes (MLflow sync, SQLAlchemy flush).
- `commit()` y `rollback()` ya están wrapped en `run_in_threadpool` dentro del UoW, no en los UCs.

### UC online (`OnlinePrediction`)
- `build_prediction_record` extraído a `services/prediction/helpers/record_builder.py` — compartido con batch, recibe `source: SourceType` como parámetro.

### UC batch (`BatchPrediction`)
- Firma de entrada: `messages: list[tuple[uuid.UUID, PredictionRequest]]` — el consumer arma el objeto Pydantic y lo pasa con un ID de correlación.
- Firma de salida: `BatchPredictionResult` (Pydantic schema, no dataclass) con:
  - `predictions: list[tuple[uuid.UUID, float]]` — (correlation_id, predicted_price) para publicar al topic `price-predicted`.
  - `failed: list[tuple[uuid.UUID, PredictionRequest]]` — para re-encolar al topic `listing-created`.
- Happy path: `batch_add` con `ON CONFLICT DO NOTHING` + un solo `commit()`.
- Fallback: `begin_nested()` por fila + `rollback_to_savepoint()` en los que fallan + un solo `commit()` al final — no un commit por fila.
- Errores del modelo propagan sin capturar — el consumer re-encola el batch entero.

### `ON CONFLICT DO NOTHING` en `batch_add`
- Kafka es at-least-once: si el consumer muere después del INSERT y antes de commitear el offset, reintenta el mismo batch. `ON CONFLICT DO NOTHING` evita duplicados en ese caso.
- Usa `sqlalchemy.dialects.postgresql.insert().on_conflict_do_nothing()` + `session.execute()` directo — sin `session.flush()` posterior (solo necesario con el ORM, no con DML directo).

### principal en el flujo batch/Kafka
- El `principal` que recibe el UC es un **system ID fijo** (`SYSTEM_PRINCIPAL_ID`) configurado vía env var en `settings.py` — representa a `properties-service` como actor del flujo server-to-server, no a un usuario real.

### `ModelClient.batch_predict`
- Construye un DataFrame multi-fila y llama `model.predict(df).tolist()` — no `.iloc[0]` que solo devuelve el primer resultado.

## Open questions

- Mecanismo concreto de mensajería (Kafka vs alternativa) y nombres de topics aún sin decidir.
- `SYSTEM_PRINCIPAL_ID` no está todavía en `settings.py`.

## Next steps

- Alembic migration para crear la tabla `predictions`.
- Agregar `SYSTEM_PRINCIPAL_ID: uuid.UUID` a `settings.py`.
- Agregar `analytics-ms-db` al `docker-compose.yml` (gap #1 del runbook).
- Implementar el consumer del topic `listing-created` en `workers/`.
