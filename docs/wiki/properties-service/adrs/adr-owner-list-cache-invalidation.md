---
title: ADR-0006 — Invalidación por prefijo del cache de la vitrina pública (offset en la key)
status: stable
last-verified: 2026-07-13
owners: [properties-service]
related:
  - "[[properties-service-listing]]"
  - "[[adr-cache-optional-layer]]"
  - "[[properties-service-architecture]]"
sources: [../../../sources/properties-service/2026-06-22-public-storefront-cache-invalidation.md]
decision-date: 2026-06-22
decision-status: accepted
---

# ADR-0006 — Invalidación por prefijo del cache de la vitrina pública (offset en la key)

## Contexto

La vitrina pública de un publicante (`GET /v1/properties/users/{user_id}`, `GetPublicUserPropertiesUseCase`) devuelve sus propiedades `active` paginadas por **offset** (`LIMIT/OFFSET`, `PUBLIC_PROPERTIES_PAGE_SIZE = 21` — 20 de página real + 1 extra para detectar `has_more` sin `COUNT(*)`, ver [[properties-service-listing]]). Se le agregó cache-aside. Dos decisiones acopladas:

1. **Granularidad del cache** frente a la paginación: ¿una entrada por página (offset en la key) o una sola entrada con la lista completa y slice en memoria?
2. **Cómo invalidar** cuando el dueño cambia una propiedad, dado que el set público es dinámico.

## Decisión

- **Offset a nivel query, una entrada de cache por página**: key `properties:user:{id}:public:{offset}` (helper `public_user_properties(user_id, offset)`). Sin el offset en la key, la página 2 devolvería la data cacheada de la página 1.
- **Se cachea también el resultado vacío** (`if cached is not None`, no `if cached`) para evitar cache penetration de usuarios sin listings — `[]` es un hit válido.
- **Invalidación por prefijo**: `delete_pattern(properties:user:{id}:public:*)` borra **todas** las páginas del dueño y deja que se re-cacheen on-demand. `delete_pattern` usa `SCAN` iterativo (no `KEYS`, que bloquea Redis) + `DEL`, expuesto en `CacheClient` → `CachePort` → `RedisCacheAdapter`.
- **Por qué prefijo y no key exacta**: con paginación por offset, un cambio de membresía corre la posición de **todas** las propiedades siguientes → desalinea todas las páginas, no solo la que contiene la propiedad afectada. Y no se trackea en qué offset cayó cada una. Borrar el prefijo completo es lo correcto, no solo lo cómodo.

## Alternativas descartadas

- **Cachear la lista completa bajo una key (`properties:user:{id}:public`) y cortar la página en memoria.** Invalidación trivial (una key exacta, idéntica a `client_properties`), sin tocar el cache client. Se descartó porque se prefirió paginar a nivel query; el set acotado (~20 activas por publicante) hace que el costo del wipe por prefijo sea bajo. **Es la alternativa a revisitar si la invalidación multi-key se vuelve un problema.**
- **Trackear los offsets activos en un set aparte** para borrarlos puntualmente. Más estado y complejidad que el `SCAN` por prefijo, sin beneficio a esta escala.
- **`KEYS pattern` en vez de `SCAN`.** Descartado: `KEYS` bloquea el server mientras barre el keyspace; nunca en runtime.

## Consecuencias

- ✅ Paginación servida desde cache por página; usuario sin listings no toca DB (vacío cacheado).
- ✅ Invalidación correcta ante corrimiento de páginas — no quedan páginas desalineadas.
- ❌ La invalidación es un **wipe del prefijo** del dueño en cada escritura relevante (vs una key exacta con la alternativa de lista completa).
- ❌ Cacheando vacíos + offset en la key, offsets arbitrarios (`?offset=99999`) pueblan entradas vacías en Redis. Acotado por el TTL (`CACHE_TTL_USER_PROPERTIES_SECONDS` = 30 min).
- ❌ Sobre un `draft`, los UCs de escritura igual corren el `delete_pattern` (wipe de más, inofensivo) — se aceptó no ramificar por status.

## Claims

- La cache key de la vitrina pública incluye el offset: `properties:user:{id}:public:{offset}` ([cache_keys.py](backend/properties-service/src/app/services/shared/helpers/cache_keys.py)).
- `GetPublicUserPropertiesUseCase` cachea también el resultado vacío y lo trata como hit con `if cached is not None` ([get_public_user_properties.py](backend/properties-service/src/app/services/listing/use_cases/property_core/get_public_user_properties.py)).
- `CacheClient.delete_pattern` usa `scan_iter` + `delete(*keys)` con guard de lista vacía, degradando a no-op si Redis falla ([cache.py](backend/properties-service/src/app/integrations/cache/redis/cache.py)).
- `delete_pattern` está expuesto en el port `CachePort` y el adapter `RedisCacheAdapter` ([cache.py](backend/properties-service/src/app/services/shared/ports/cache.py), [redis_cache_adapter.py](backend/properties-service/src/app/services/shared/adapters/redis_cache_adapter.py)).
- 8 UCs de escritura invalidan `public_user_properties_pattern(owner)` junto a sus keys exactas; `verify` y `create_property` quedan excluidos ([cache_keys.py](backend/properties-service/src/app/services/shared/helpers/cache_keys.py)).
