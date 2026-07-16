---
title: ADR-0006 — Librería interna compartida para clientes de infra (Redis/MinIO)
status: stable
last-verified: 2026-07-15
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[open-items]]"
  - "[[adr-cache-optional-layer]]"
  - "[[catalog-service-architecture]]"
  - "[[properties-service-architecture]]"
  - "[[users-service-architecture]]"
sources: []
decision-date: 2026-06-12
decision-status: accepted
---

## TL;DR

Los clientes de infraestructura (Redis, MinIO, y a futuro otros como el dep de auth JWT/cookie) se centralizan en un paquete interno del monorepo (`backend/_lib/`) instalado por path con uv workspace. Los **ports se quedan en cada servicio** (el contrato pertenece al consumidor); lo compartido es solo el adapter/cliente y las excepciones base. Regla dura de scope: **solo infra, nunca lógica ni schemas de dominio**. Pendiente de implementación — ver [[open-items]].

## Contexto

Cada microservicio copia su propio stack de cache y storage:

- **Redis** por triplicado en catalog, properties y users: `integrations/cache/redis/cache.py` + `services/shared/adapters/redis_cache_adapter.py` + `services/shared/ports/cache.py` + `core/exceptions/cache.py`.
- **MinIO** por duplicado en properties y users: `integrations/storage/minio/storage.py` + adapter + port + exceptions.

Las copias **ya divergieron** (verificado 2026-06-12, ningún hash coincide entre servicios): el port de cache de users tiene los 7 métodos base, catalog agrega `set_nx`, properties agrega `mget`/`mget_json`/`mset`/`mset_json` y `delete` multi-key. En storage la divergencia es funcional: properties expone presigned PUT URLs y users hace `upload_file` server-side. Un bugfix o mejora en una copia no se propaga a las demás salvo copy-paste manual.

La objeción clásica a shared libs en microservicios (acoplan equipos, rompen deployabilidad independiente) asume N equipos con ciclos de release propios. Aquí hay un solo dev en un monorepo con commits atómicos: actualizar la lib y los N servicios en el mismo commit es un solo diff, no coordinación entre equipos.

## Decisión

Crear un paquete interno `backend/_lib/` (nombre del package a definir al implementar) que centraliza:

1. **Cliente Redis** — superset de métodos de las tres copias actuales (base + `set_nx` + familia `mget`/`mset` + `delete` multi-key).
2. **Cliente MinIO** — expone **ambas** estrategias (presigned PUT URLs y `upload_file` server-side); la divergencia actual no es accidental, son dos operaciones legítimas y cada servicio usa la suya.
3. **Excepciones base** de cache y storage.

Mecanismo de instalación: **uv workspace** (dependencia por path dentro del monorepo) — es el feature de uv diseñado para esto y evita publicar a un registry.

Reglas que sostienen la decisión:

- **Los ports se quedan en cada servicio.** El contrato le pertenece al consumidor (hexagonal): que users declare un port de 7 métodos aunque la lib ofrezca 12 es correcto — consume lo que necesita. Lo que se centraliza es el adapter/cliente, no el contrato del dominio.
- **Scope infra-only (regla dura).** Cache, storage, y candidatos futuros del mismo tipo (auth dep JWT/cookie, logging estructurado). Nunca schemas, entidades ni lógica de dominio "porque dos servicios la usan" — ahí muere la arquitectura.
- La lib respeta [[adr-cache-optional-layer]]: el cliente Redis centralizado mantiene la semántica de degradación silenciosa.

## Alternativas consideradas

- **Dejar las copias y sincronizar a mano** — es el statu quo; el drift ya demostró que la sincronización manual no ocurre.
- **Template/scaffolding sync (copier, cookiecutter)** — sincroniza archivos pero cada servicio sigue siendo dueño de su copia; los conflictos de merge en archivos divergidos son peores que un import.
- **Publicar a un registry privado (PyPI interno)** — versionado independiente formal, pero agrega infraestructura (registry, releases, bump de versiones) que un dev solo no amortiza; uv workspace da lo mismo sin ceremonia.
- **Mover también los ports a la lib** — menos duplicación aparente, pero acopla los contratos de dominio de N servicios a una definición central; rompe el principio de que el port pertenece al consumidor.

## Consecuencias

- **Positivo**: un bugfix en el cliente Redis/MinIO llega a todos los servicios en el mismo commit.
- **Positivo**: el superset de métodos queda disponible para todos (p. ej. catalog gana `mget_json` sin copy-paste).
- **Negativo / coste principal**: los **Dockerfiles** deben ajustarse — hoy cada servicio construye con su carpeta como build context; una dependencia por path obliga a subir el contexto a `backend/` (o configurar uv workspace en el build). Es el ~80 % del esfuerzo del refactor; el código de la lib es trivial.
- **Negativo**: un cambio breaking en la lib obliga a actualizar N servicios en lockstep (aceptable con un solo dev y commits atómicos; re-evaluar si el equipo crece).
- **A futuro**: candidatos de segunda ola — auth dep (JWT/cookie), logging estructurado JSON ([[open-items]] § Observabilidad), correlation_id middleware.

## Claims

- El stack de cache Redis (client + adapter + port + exceptions) está copiado en catalog, properties y users, y los ports ya divergieron ([catalog ports/cache.py](backend/catalog-service/src/app/services/shared/ports/cache.py), [properties ports/cache.py](backend/properties-service/src/app/services/shared/ports/cache.py), [users ports/cache.py](backend/users-service/src/app/services/shared/ports/cache.py)).
- El stack de MinIO está copiado en properties y users con ports funcionalmente distintos: presigned PUT URLs vs `upload_file` server-side ([properties ports/storage.py](backend/properties-service/src/app/services/shared/ports/storage.py), [users ports/storage.py](backend/users-service/src/app/services/shared/ports/storage.py)).
- `backend/_lib/` no existe al 2026-06-12 — la decisión está aceptada pero sin implementar; el ítem vive en [[open-items]].
- analytics-service no tiene stack de cache Redis propio al 2026-06-12 — será consumidor directo de la lib cuando lo necesite.
