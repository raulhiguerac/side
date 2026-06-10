---
title: analytics-service
status: draft
last-verified: 2026-05-26
owners: [analytics-service]
related:
  - "[[architecture]]"
  - "[[analytics-service-architecture]]"
  - "[[analytics-service-prediction]]"
  - "[[avm-training]]"
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md, ../../sources/analytics-service/2026-05-20-prediction-wiring-and-batch-uc.md, ../../sources/analytics-service/2026-05-26-predict-endpoint-form-design.md]
---

## TL;DR

Microservicio responsable de **inteligencia analítica** sobre el marketplace: predicción de precio de propiedades (AVM) e insights de mercado (B2B). Sirve a usuarios finales (predicciones sincrónicas vía `/predict`) y a otros servicios del backend (predicciones async para enriquecer listings).

## Por qué existe

El producto requiere dos jobs distintos que se separan en este servicio:

1. **Saber cuánto vale una propiedad** dada sus features. Es input para:
   - El badge de precio del feed (🟢 fair / 🟡 alto / 🔴 muy alto)
   - La calculadora pública de valuación (un usuario quiere saber qué cuesta su inmueble)
   - El enriquecimiento automático del campo `estimated_price` al crear un listing
2. **Entender cómo se mueve el mercado** para producir insights (B2B, dashboards, reportes), generalmente vía agregados sobre snapshots periódicos.

## Dominios

| Dominio | Estado | Qué hace |
|---|---|---|
| `prediction` | implementado parcial | Estima precio de **venta** de una propiedad vía modelo AVM servido desde [[glossary#mlflow]]. Hoy sincrónico vía `/predict`. Arriendos a futuro. |
| `market` | scaffoldeado vacío | Jobs batch sobre snapshots para heatmap (precios + listings), neighborhood reports, anomaly detection. [[glossary#reverse-etl]] a Redis + BD. |

Cada dominio sigue el [[glossary#hex-pattern-arquitectura-hexagonal]] estándar del backend: `services/<domain>/{use_cases, ports, adapters, schemas, services, helpers}`.

## Consumers

### `/predict` sincrónico (HTTP REST)
- Hoy: usuarios registrados (JWT obligatorio resuelto a [[glossary#principal]]).
- Futuro: posible público sin login con rate limit (~2 calls/IP rolling 2h, vía Redis) para SEO/traffic driver.
- **Estado actual (2026-05-26):** UC `OnlinePrediction` implementado, route expuesta, DI completamente wired (`deps/prediction.py`), migración Alembic aplicada. Listo para consumir.

### Consumer async (`listing-created`)
Server-to-server con `properties-service` para enriquecer `estimated_price` de listings recién creados:

```
properties-service crea listing
    → publica en topic "listing-created"
        → analytics-service consume (batch, cada 15 min)
            → BatchPrediction.execute
                → publica en topic "price-predicted"
                    → properties-service consume y actualiza estimated_price
```

En este flujo el [[glossary#principal]] del UC es un **system ID** (no el usuario que creó el listing), porque es feedback al modelo, no acción del usuario.

Decisiones de diseño acordadas (2026-05-20): **confluent-kafka**, micro-batch de 15 min, proceso separado long-running (mantiene el modelo en memoria), DLQ acotado a errores de deserialización. Ver [[analytics-service-kafka-consumer]].

## Boundaries — lo que analytics-service **NO** hace

- **No resuelve geo**: `barrio_ideca` viene en el request, ya resuelto por `properties-service` (principio "geo-enrichment at write time").
- **No decide qué modelo sirve**: el alias `production` en MLflow lo setea el data team. Ver `[[adr-model-promotion-external-to-service]]`.
- **No entrena modelos**: el training vive en `data/ml/AVM/`, fuera del backend. Ver `[[adr-training-separated-from-runtime]]`.
- **No persiste listings**: la fuente de verdad de propiedades vive en `properties-service`. Analytics solo guarda los registros de predicciones (tabla `predictions`) para auditoría y feedback al modelo.
- **No emite tokens**: auth la centraliza `users-service`/Keycloak. Analytics consume el JWT vía dependency.

## Stack

- **FastAPI + Uvicorn** — HTTP layer
- **SQLModel + Postgres** — persistencia de `predictions`
- **MLflow** — model registry + tracking + serving del modelo
- **MinIO** — artifact storage de MLflow (S3-compatible self-hosted)
- **Redis** — futuro: rate limit + reverse ETL del heatmap
- **Workers** — futuro: consumer async

Stack declarado en [pyproject.toml](backend/analytics-service/pyproject.toml). El servicio carga el modelo de MLflow al startup (no on-demand) — ver [[analytics-service-architecture]].

## Roadmap inmediato

- [x] Exponer route `/predict` en `api/main.py` ✓ 2026-05-20
- [x] Dependency FastAPI para resolver JWT → `principal` (`api/deps/auth.py`) ✓ 2026-05-20
- [x] Migración Alembic para crear tabla `predictions` ✓ 2026-05-25
- [x] Implementar consumer del topic `listing-created` (workers/) ✓ 2026-05-22
- [ ] `analytics-ms-db` en `docker-compose.yml`
- [ ] Form frontend AVM: Mapbox autocomplete → catalog geo-resolution → `POST /predict`
- [ ] Agregar campo `address` a `PredictionRequest` + migración
- [ ] Endpoint de feedback de satisfacción post-predicción (alimenta campo `feedback`)
- [ ] Primer job batch del dominio `market` (heatmap)

## Related

- [[architecture]] — visión del monorepo y patrones cross-cutting
- [[analytics-service-architecture]] — arquitectura interna del servicio
- [[analytics-service-prediction]] — dominio prediction en detalle
- [[avm-training]] — pipeline de training (vive en `data/ml/AVM/`)
- [[analytics-service-local-dev]] — runbook de dev local

## Claims

- `analytics-service` contiene dos dominios scaffoldeados en `src/app/services/`: `prediction` y `market` ([services/](backend/analytics-service/src/app/services)).
- El dominio `market` está scaffoldeado pero los archivos de UCs/adapters/ports están vacíos al 2026-05-19.
- El UC `OnlinePrediction` está expuesto en `POST /v1/predict` desde 2026-05-20 — `api/main.py` incluye `health.router` y `predict.router` ([api/main.py](backend/analytics-service/src/app/api/main.py)).
- La tabla `predictions` persiste los inputs del request + `predicted_price` + `model_version` + un campo `feedback` opcional ([models/prediction.py:46](backend/analytics-service/src/app/models/prediction.py#L46)).
- El consumer async `listing-created` está implementado en `workers/listing_created/` con `ListingConsumer` y `ListingWorkerRunner` al 2026-05-22.
- Redis está declarado en dependencies pero no se usa en código todavía.
- analytics-service no resuelve `(lat, lon) → barrio_ideca`; lo recibe ya resuelto en `PredictionRequest` ([schemas/prediction.py:21](backend/analytics-service/src/app/services/prediction/schemas/prediction.py#L21)).
- La migración Alembic de `predictions` existe al 2026-05-25: `976082b7f322_first_migration_including_predictions_.py`.
