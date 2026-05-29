---
title: Arquitectura del monorepo
status: draft
last-verified: 2026-05-28
owners: [_shared]
related: [[glossary]], [[dev-workflow]], [[adr-auth-keycloak-jwt]], [[adr-geo-enrichment-at-write-time]]
sources: [../../sources/analytics-service/2026-05-19-foundational-qa.md]
---

## TL;DR

`side` es un monorepo de marketplace inmobiliario. Backend Python (FastAPI + SQLModel + arquitectura hexagonal), frontend Vue 3 + Pinia + Tailwind, training ML separado en `data/ml/`. Microservicios se comunican mayormente HTTP REST sincrónico; `analytics-service` introduce el primer flujo asíncrono vía mensajería. Auth centralizada en [[#keycloak]] con JWT.

## Layout del repo

```
side/
├── backend/                  # microservicios FastAPI
│   ├── users-service/
│   ├── catalog-service/
│   ├── properties-service/
│   └── analytics-service/
├── frontend/                 # SPA Vue 3
├── data/                     # workloads ML, EDA, training
│   └── ml/AVM/
├── docs/                     # este wiki
├── .devcontainer/            # dev container definition
└── docker-compose.yml        # orquestación local
```

## Microservicios

| Servicio | Responsabilidad | Estado |
|---|---|---|
| `users-service` | Auth (gateway de [[glossary#keycloak]]), perfiles, roles | en desarrollo |
| `catalog-service` | Geo catalog (países, localidades, barrios [[glossary#ideca]]), POIs vía Overpass/OSM | en desarrollo |
| `properties-service` | CRUD de propiedades, listings, RBAC, feed, geo-enrichment al crear listing | en desarrollo |
| `analytics-service` | Predicción AVM + insights de mercado (B2B) | en desarrollo |
| `notifications-service` | _planificado, no creado_ | — |
| `payments-service` | _planificado, no creado_ | — |

### Frontend
- **Vue 3 SPA** con estructura views + componentes reusables.
- **Pinia** para state management.
- **Composables** para lógica reutilizable entre views.
- **Tailwind** para estilos.

### Workloads ML
`data/ml/AVM/` aloja el pipeline de training del modelo AVM. **Separado del backend** para aislar responsabilidades data team / runtime team. La comunicación entre ambos lados ocurre vía [[glossary#mlflow]] (registry + alias `production`). Ver `[[adr-training-separated-from-runtime]]`.

## Patrón hexagonal (en backend services)

Cada microservicio del backend sigue el mismo layout interno:

```
src/app/
├── api/                      # routes, middleware, exception handlers
│   ├── deps/                 # FastAPI dependencies (auth, db, etc.)
│   ├── handlers/
│   ├── middleware/
│   └── routes/
├── core/                     # config, logging, exceptions base
├── db/                       # session, engine
├── integrations/             # clientes a infra externa (Redis, MinIO, Mapbox, MLflow…)
├── models/                   # SQLModel entities
├── services/<domain>/        # un dominio por subcarpeta
│   ├── adapters/             # implementaciones concretas de los ports
│   ├── ports/                # Protocols (interfaces)
│   ├── schemas/              # Pydantic DTOs del dominio
│   ├── services/             # lógica de dominio interna
│   ├── use_cases/            # casos de uso (entry points)
│   └── helpers/
├── workers/                  # consumers async (Kafka u otro)
└── main.py
```

**Regla:** los use cases dependen de **ports** (Protocols), nunca de adapters concretos. Los adapters se inyectan en los UCs vía `Depends(...)` de FastAPI en el `api/deps/` layer.

## Patrones de comunicación

### Síncrono (HTTP REST) — default
Casi todas las llamadas entre servicios son HTTP REST hoy. El JWT del usuario se propaga en la cookie `access_token` (todos los servicios la leen de la cookie, no del header `Authorization`). Ejemplos:
- frontend → cualquier microservicio
- properties-service → users-service para validar permisos
- properties-service → catalog-service para resolver geo

### Asíncrono — solo `properties` ↔ `analytics` (en definición)
Único flujo async planificado hoy. Caso de uso: cálculo de `estimated_price` para un listing recién creado.

```
properties-service              [topic: listing-created]              analytics-service
   |  (publica listing nuevo)─────────────────────────►  (consume mensaje, predice)
                                                                       |
                                                                       ▼
   ◄────────────────────────  [topic: price-predicted]  ─────────────  (publica resultado)
(consume y actualiza
 estimated_price del listing)
```

- Mecanismo concreto (Kafka u otro) **aún no decidido**. El scaffolding `src/app/workers/` en analytics-service anticipa la implementación.
- En este flujo el [[glossary#principal]] que llega al UC de analytics es un **system ID**, no el usuario que creó el listing — el caso es feedback al modelo, no acción del usuario.

## Decisiones cross-cutting

### Auth: Keycloak + JWT
[[glossary#keycloak]] es el identity provider central. `users-service` actúa como gateway de auth. Cada microservicio del backend tiene una FastAPI dependency que resuelve el JWT y entrega un `principal: uuid.UUID` al UC — los use cases nunca ven el token. Ver `[[adr-auth-keycloak-jwt]]`.

### Cloud-agnostic
Sin créditos en ninguna nube hoy. Stack elegido para correr en cualquier docker host: MLflow + MinIO en vez de SageMaker/Vertex; Postgres + Redis + Keycloak self-hosted. Decisión que puede revisarse cuando haya créditos o partnership con una nube.

### Geo-enrichment at write time
La resolución `(lat, lon) → barrio_ideca` ocurre **al crear el listing en `properties-service`**, no al consumirlo en analytics u otros servicios. Principio: enriquecimiento geográfico al momento de escribir, no leer. Reduce calls de red en el path crítico de cada lectura y permite cachear/indexar por barrio. Ver `[[adr-geo-enrichment-at-write-time]]`.

### Dev environment unificado
Todo el desarrollo local ocurre dentro de un [[glossary#devcontainer]] levantado por `docker-compose.yml` en el root. Los servicios no contaminan el host del developer. Ver el runbook de cada servicio (ej: `[[analytics-service-local-dev]]`).

## Claims

- El backend está en `backend/<service>/` con un subdirectorio por microservicio.
- El frontend Vue vive en `frontend/`.
- El training ML vive en `data/ml/AVM/`, fuera de `backend/`.
- Cada servicio backend sigue el layout `src/app/{api,core,services/<domain>/{adapters,ports,schemas,use_cases},...}` (verificable comparando estructuras de `catalog-service` y `analytics-service`).
- Los ports en `services/<domain>/ports/` están declarados como `typing.Protocol` (ver [model_gateway.py:6](backend/analytics-service/src/app/services/prediction/ports/model_gateway.py#L6)).
- La comunicación entre servicios es HTTP sincrónico, excepto el flujo async entre `properties-service` y `analytics-service` (aún sin código de consumer al 2026-05-19).
- Auth centralizada en Keycloak; cada UC recibe `principal: uuid.UUID` resuelto por una FastAPI dependency.
- `barrio_ideca` se resuelve en `properties-service` y se propaga río abajo; analytics-service lo recibe como dato del request, no lo resuelve.
- `notifications-service` y `payments-service` están planeados pero no implementados al 2026-05-19 (no existen en `backend/`).
- `docker-compose.yml` vive en el root del monorepo y levanta todos los servicios + el devcontainer.
