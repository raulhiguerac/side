---
title: Worker — compensación de Keycloak (users-service)
status: draft
last-verified: 2026-05-28
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-auth]]"
  - "[[users-service-keycloak]]"
  - "[[adr-keycloak-saga-compensation]]"
  - "[[adr-apscheduler-in-process-worker]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Job periódico que borra de Keycloak los usuarios huérfanos — los que se crearon en el IdP pero cuyo `Account` local no se persistió (registro fallido). Lee la cola `kc_compensation_tasks`, reintenta el delete con backoff exponencial + jitter, y marca `done`/`failed`. Corre **dentro del proceso FastAPI** vía APScheduler cada 15 min.

## Por qué existe

El registro es una saga entre dos sistemas sin transacción común (Keycloak + DB). Si la DB falla tras crear el usuario en Keycloak, el [[users-service-auth|dominio auth]] intenta borrarlo inline; si ese borrado también falla (IdP caído), encola un `KcCompensationTask`. Este worker es el reintento async que garantiza consistencia eventual. Ver [[adr-keycloak-saga-compensation]].

## Cómo corre

`core/scheduler.py` arranca un `AsyncIOScheduler` en el `lifespan` de la app:

```python
scheduler.add_job(
    run_job, trigger="interval", seconds=900,
    id="kc_compensation", max_instances=1,
    coalesce=True, misfire_grace_time=60,
)
```

- `max_instances=1` + `coalesce=True` → nunca corren dos ejecuciones en paralelo; si se acumulan disparos, se colapsan en uno.
- `run_job` salta a un thread (`asyncio.to_thread`) porque el acceso a DB y el cliente de Keycloak son síncronos.

## Procesamiento (`retry_keycloak_deletions`)

1. Selecciona hasta `BATCH_SIZE` (25) tasks con `status=pending`, `attempts < MAX_ATTEMPTS` (5), y `next_retry_at <= now`.
2. Por cada task, `KeycloakAdminClient.delete_account(kc_user_id)`:
   - **Éxito** → `status=done`, `last_error=None`.
   - **Fallo** → `attempts += 1`, registra `last_error`, calcula `next_retry_at = now + min(60, 2**attempts) min + jitter(0-30s)`. Si `attempts >= MAX_ATTEMPTS` → `status=failed`.
3. Commit por task (un fallo de DB en una no aborta el resto).

## Parámetros

| Constante | Valor | Para qué |
|---|---|---|
| `MAX_ATTEMPTS` | 5 | Tras 5 intentos la task pasa a `failed`. |
| `BATCH_SIZE` | 25 | Tasks por ciclo. |
| `MAX_DELAY_MIN` | 60 | Cap del backoff exponencial (minutos). |
| intervalo | 900s | Frecuencia del scheduler. |

## Contraste con analytics-service

El consumer de [[analytics-service-kafka-consumer]] corre en un **proceso separado** porque mantiene un modelo ML pesado en memoria entre ciclos. Acá no hay estado caro que preservar, así que el worker vive **in-process** en FastAPI — más simple de desplegar (un solo contenedor) a costa de acoplar su ciclo de vida al del web server. Ver [[adr-apscheduler-in-process-worker]].

## Claims

- El job corre vía APScheduler en el lifespan con `interval` de 900s, `max_instances=1`, `coalesce=True` ([scheduler.py:19-27](backend/users-service/src/app/core/scheduler.py#L19-L27)).
- `run_job` ejecuta el trabajo síncrono en un thread con `asyncio.to_thread` ([keycloak_tasks.py:19-24](backend/users-service/src/app/workers/keycloak_tasks.py#L19-L24)).
- Selecciona tasks `pending` con `attempts < MAX_ATTEMPTS` y `next_retry_at <= now`, hasta `BATCH_SIZE` ([keycloak_tasks.py:28-34](backend/users-service/src/app/workers/keycloak_tasks.py#L28-L34)).
- El backoff es `min(60, 2**attempts)` minutos + jitter de 0-30s ([keycloak_tasks.py:60-62](backend/users-service/src/app/workers/keycloak_tasks.py#L60-L62)).
- Tras `MAX_ATTEMPTS` (5) la task pasa a `status=failed` ([keycloak_tasks.py:64-65](backend/users-service/src/app/workers/keycloak_tasks.py#L64-L65)).
- `BATCH_SIZE=25`, `MAX_ATTEMPTS=5`, `MAX_DELAY_MIN=60` ([keycloak_tasks.py:14-16](backend/users-service/src/app/workers/keycloak_tasks.py#L14-L16)).
- Cada task se commitea por separado; un error de DB en una no aborta el batch ([keycloak_tasks.py:79-87](backend/users-service/src/app/workers/keycloak_tasks.py#L79-L87)).
