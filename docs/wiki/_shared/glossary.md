---
title: Glosario compartido
status: draft
last-verified: 2026-05-19
owners: [_shared]
related: [[architecture]]
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

Términos del proyecto `side` (negocio, dominio inmobiliario, infra) que son **cross-cutting** entre servicios. Los términos específicos de un servicio viven en su propio glossary (ej: `[[analytics-service-glossary]]`).

## Términos

### AVM (Automated Valuation Model)
Modelo estadístico/ML que estima el valor de mercado de una propiedad a partir de features (área, ubicación, estrato, tipo, año, POIs cercanos). El AVM de `side` se entrena en `data/ml/AVM/` y se sirve desde [[analytics-service]] vía MLflow registry.

### barrio_ideca
Identificador normalizado del barrio de Bogotá según el estándar [[#ideca]]. Aparece como campo de request en `/predict` y como columna en la tabla `predictions`. Su valor lo resuelve `properties-service` al crear el listing (geocoding desde `lat/lon`), nunca lo resuelve `analytics-service`. Ver `[[adr-geo-enrichment-at-write-time]]`.

### Devcontainer
Container de desarrollo definido en `.devcontainer/` que aloja todo el entorno local (Python, Node, deps, herramientas). Se levanta vía `docker-compose.yml` en el root del monorepo. Los microservicios corren **dentro del devcontainer** para no instalar nada en el host del desarrollador.

### estimated_price
Campo de un listing en `properties-service` que contiene el precio sugerido por el modelo AVM. Lo escribe `properties-service` después de recibir la predicción async desde [[analytics-service]] — analytics nunca escribe directo en la BD de properties.

### Hex pattern / Arquitectura hexagonal
Patrón de diseño que separa los **use cases** del dominio de los **adapters** (DB, HTTP clients, etc.) vía **ports** (interfaces `typing.Protocol`). Cada microservicio del backend usa este patrón: `services/<domain>/{use_cases, ports, adapters, schemas}`. Ver [[architecture]] para el layout completo.

### IDECA
Infraestructura de Datos Espaciales de Bogotá (https://www.ideca.gov.co/). Estándar oficial del distrito para datos geográficos, incluyendo la nomenclatura de barrios. El proyecto usa IDECA como source-of-truth para todo lo geo en Bogotá.

### Keycloak
Identity provider self-hosted. Emite los JWT que autentican todas las requests autenticadas del sistema. Centralizado alrededor de `users-service` que actúa como gateway. Cada microservicio backend tiene una FastAPI dependency que resuelve el JWT al [[#principal]]. Ver `[[adr-auth-keycloak-jwt]]`.

### MLflow
Plataforma open-source de MLOps. En `side` cumple tres roles: (a) tracking de experimentos de training, (b) artifact storage (modelos serializados, métricas, plots) backed por [[#minio]], (c) model registry con aliases (`production`, `staging`). Servidor self-hosted. Es el **contrato** entre el data team (entrena, promueve) y el runtime (consume el alias `production`).

### MinIO
Servidor S3-compatible self-hosted. En `side` actúa como artifact store de [[#mlflow]] (almacena los modelos serializados y artefactos de cada run). Self-hosted para mantener el stack cloud-agnostic.

### Monorepo
Estructura del repo: un único repositorio Git que aloja `backend/`, `frontend/`, `data/` y `docs/`. Servicios independientes pero compartiendo CI, conventions y este wiki.

### POI (Point of Interest)
Punto geográfico con atributos categorizables (escuela, parque, hospital, transporte). Usados como features del AVM (distancia a POIs cercanos). Hoy se generan desde un CSV manual extraído de OpenStreetMap; futuro: tabla poblada por `catalog-service` desde Overpass, eventualmente DWH.

### principal
UUID que identifica al actor que origina una request — usualmente un usuario, pero también puede ser un sistema (system ID) en flujos server-to-server (ej: el consumer Kafka de `analytics-service`). Se obtiene resolviendo el JWT vía una FastAPI dependency. Los use cases reciben el `principal` ya resuelto, nunca el token.

### `production` (alias MLflow)
Alias en el [[#mlflow]] registry que apunta al model version actualmente en producción. `analytics-service` siempre lee del alias, nunca de una versión hardcodeada. La promoción de un modelo a `production` es responsabilidad del data team — analytics no decide qué modelo sirve. Ver `[[adr-model-promotion-external-to-service]]`.

### Reverse ETL
Patrón de mover datos **desde** un data store analítico **hacia** sistemas operacionales (BD transaccional, caché, herramientas SaaS). En `side`, los jobs batch del dominio `market` (heatmap, neighborhood reports) computan agregados y los publican a Redis + BD para que la app los consuma en tiempo de request sin recomputar.

### Snapshot
Captura periódica del estado del mercado (listings activos, precios, días en mercado, demanda) que alimenta los insights del dominio `market` de [[analytics-service]]. Se procesan en batch para generar agregados, heatmaps y reportes B2B.

## Claims

- `barrio_ideca` aparece como columna en la tabla `predictions` y como campo de `PredictionRequest` ([prediction.py](backend/analytics-service/src/app/services/prediction/schemas/prediction.py)).
- IDECA es el estándar oficial del distrito de Bogotá para datos espaciales (https://www.ideca.gov.co/).
- El modelo servido por `analytics-service` se determina por el alias `production` en MLflow, no por versión explícita ([avm_model_adapter.py:10](backend/analytics-service/src/app/services/prediction/adapters/avm_model_adapter.py#L10)).
- POIs hoy se extraen desde CSV de OpenStreetMap (input del CLI de training en `data/ml/AVM/train.py`).
- `notifications-service` y `payments-service` no están implementados al 2026-05-19.
- Los UCs reciben `principal: uuid.UUID`, no el token JWT ([online.py:44](backend/analytics-service/src/app/services/prediction/use_cases/online.py#L44)).
