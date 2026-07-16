---
title: ADR-0002 — Worker de compensación in-process con APScheduler
status: stable
last-verified: 2026-07-15
owners: [users-service]
related:
  - "[[users-service-kc-compensation]]"
  - "[[users-service-architecture]]"
  - "[[analytics-service-kafka-consumer]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0002 — Worker de compensación in-process con APScheduler

## Contexto

El reintento de borrados de Keycloak ([[users-service-kc-compensation]]) necesita correr periódicamente. Hay dos formas en el monorepo: un proceso separado long-running (como el consumer Kafka de [[analytics-service-kafka-consumer]]) o un scheduler embebido en el proceso FastAPI. La pregunta es dónde vive este job.

## Decisión

- **APScheduler (`AsyncIOScheduler`) embebido en el lifespan de FastAPI**. El scheduler arranca al iniciar la app y se apaga al cerrarla.
- Job `interval` de 900s con `max_instances=1`, `coalesce=True`, `misfire_grace_time=60`.
- El trabajo síncrono (DB + cliente Keycloak) corre en un thread vía `asyncio.to_thread` para no bloquear el event loop.

## Alternativas consideradas

- **Proceso separado** (como analytics) — el patrón se justifica allá porque el consumer mantiene un **modelo ML pesado en memoria** entre ciclos; reiniciar el proceso por ciclo recargaría el modelo. users-service **no tiene estado caro** que preservar: cada ciclo abre una `Session`, procesa un batch chico y termina. Un proceso aparte sería overhead de despliegue sin beneficio.
- **Cron del sistema / k8s CronJob** — externaliza la planificación, pero agrega una pieza de infra y un contenedor más; innecesario para un job liviano.
- **Cola con mensajería (Kafka/SQS) + worker** — más robusto y escalable, pero el servicio no tiene mensajería; sería sobre-ingeniería para una cola de compensación de bajo volumen.

## Consecuencias

- ✅ **Un solo contenedor** para desplegar (web + worker) — operación más simple.
- ✅ Sin infra extra (ni broker, ni cron externo).
- ✅ `max_instances=1` + `coalesce` evitan solapamientos y acumulación de disparos.
- ❌ **Acoplado al ciclo de vida del web server**: si la app no está corriendo, el worker no corre; un deploy/restart pausa la compensación.
- ❌ **No escala horizontalmente sin cuidado**: con N réplicas de la app, hay N schedulers corriendo el mismo job → posible doble procesamiento. Hoy aceptable (1 réplica; el delete de Keycloak es idempotente — 404 = éxito), pero es una trampa al escalar.
- ❌ Comparte recursos (CPU/conexiones DB) con el path de requests; un batch grande podría competir con el tráfico web.
- ❌ Decisión **divergente** de analytics — dos patrones de worker en el monorepo; documentar cuál aplica cuándo (estado pesado → proceso separado; job liviano → in-process).

## Claims

- El worker corre vía `AsyncIOScheduler` en el lifespan de FastAPI ([scheduler.py:11-33](backend/users-service/src/app/core/scheduler.py#L11-L33)).
- Config del job: `interval` 900s, `max_instances=1`, `coalesce=True`, `misfire_grace_time=60` ([scheduler.py:19-27](backend/users-service/src/app/core/scheduler.py#L19-L27)).
- El trabajo síncrono se ejecuta en un thread con `asyncio.to_thread` ([keycloak_tasks.py:19-24](backend/users-service/src/app/workers/keycloak_tasks.py#L19-L24)).
- El delete de Keycloak es idempotente (404 → éxito), lo que mitiga el riesgo de doble procesamiento ([admin_client.py:104-107](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L104-L107)).
- analytics-service usa un proceso separado por su modelo ML en memoria — patrón contrastante ([[analytics-service-kafka-consumer]]).
