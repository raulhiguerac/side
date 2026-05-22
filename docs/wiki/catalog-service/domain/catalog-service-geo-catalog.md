---
title: Dominio geo_catalog (catalog-service)
status: draft
last-verified: 2026-05-21
owners: [catalog-service]
related: [[catalog-service]], [[catalog-service-architecture]], [[catalog-service-catalog-admin]]
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Dominio de **reads** del catálogo. 5 UCs que sirven al frontend (autocomplete con debounce) y a otros services (validación de IDs). Patrón uniforme: try cache → DB fallback → repopulate cache. TTL `CACHE_TTL_CATALOG_SECONDS` (1 día) para listas. Cache best-effort en todos los UCs.

## Public surface

Todos públicos (sin auth), bajo `/v1/`:

| Método | Path | UC | Cache key |
|---|---|---|---|
| GET | `/countries` | `GetCountriesUseCase` | `cache_key_countries()` |
| GET | `/localities/by-country?country_id` | `GetLocalitiesUseCase` (filter) | `cache_key_localities(country_id)` |
| GET | `/localities/by-admin-division?admin_division_id` | `GetLocalitiesUseCase` (filter) | (sin cache hoy) |
| GET | `/localities/by-id?locality_id` | `GetLocalityByIdUseCase` | `cache_key_locality(locality_id)` |
| GET | `/neighborhoods/by-locality?locality_id` (acepta múltiples) | `GetNeighborhoodsByLocalityUseCase` | `cache_key_neighborhoods(locality_id)` |
| GET | `/neighborhoods/by-id?neighborhood_id` | `GetNeighborhoodByIdUseCase` | `cache_key_neighborhood(neighborhood_id)` |

## Componentes

| Pieza | Archivo |
|---|---|
| UCs | `use_cases/get_countries.py`, `get_locality.py` (multi-filter), `get_locality_by_id.py`, `get_neighborhoods_by_locality.py`, `get_neighborhood_by_id.py` |
| Ports | `ports/countries_repository.py`, `locality_repository.py`, `neighborhood_repository.py`, `unit_of_work.py` |
| Adapters SQL | `adapters/sql_countries_repository.py`, `sql_locality_repository.py`, `sql_neighborhood_repository.py`, `sql_unit_of_work.py` |
| Helpers | `helpers/cache_keys.py` (re-export desde `shared/helpers/cache_keys.py`) |
| Schemas | `schemas/country.py`, `locality.py`, `neighborhood.py` |

`geo_catalog/helpers/cache_keys.py` re-exporta los key builders de `shared/` con `# noqa: F401`. Misma fuente de verdad que `catalog_admin` para garantizar que writes y reads invaliden/lean las mismas keys.

## Patrón de UC estándar

[`GetCountriesUseCase`](backend/catalog-service/src/app/services/geo_catalog/use_cases/get_countries.py) es el más simple y representativo:

1. **Try cache**: `cache.get_json(cache_key_countries())` en `try/except pass`. Si hit, deserializa y returns.
2. **DB fallback**: `run_in_threadpool(uow.countries.get_active_countries)`.
3. **Repopulate cache** (best-effort): `cache.set_json(key, value, ttl=CACHE_TTL_CATALOG_SECONDS)` si hubo resultados.
4. Returns `list[CountryListItem]`.

TTL = `CACHE_TTL_CATALOG_SECONDS` (1 día) — listas read-only cambian raramente (writes admin invalidan explícitamente, ver [[catalog-service-catalog-admin]]).

## Batch lookup (`GetNeighborhoodsByLocality`)

Único UC que recibe **lista** de `locality_id`. Patrón hot-cold split:

1. Por cada `locality_id`: check cache individual. Si hit, agrega a `result`. Si miss, agrega a `missing`.
2. Si `missing` vacío → return temprano sin tocar DB.
3. Una sola query para todos los `missing`: `uow.neighborhoods.get_active_by_locality_ids(locality_ids=missing)`.
4. Agrupa el resultado por `locality_id`.
5. **Cache fill por locality**: por cada `lid in missing`, guarda su lista (puede estar vacía si la locality no tiene barrios).

Optimización vs naive (N+1): si todas las localities están cacheadas, cero hits a DB. Si solo algunas faltan, una sola query batch.

## Refresh del cache

El cache lo invalidan las UCs de [[catalog-service-catalog-admin]] al escribir. Por ejemplo:
- `BulkCreateNeighborhoodsUseCase` borra `cache_key_neighborhoods(locality_id)` al final.
- `BulkEnrichNeighborhoodGeometriesUseCase` borra `cache_key_neighborhood(id)` por barrio actualizado + `cache_key_neighborhoods(locality_id)`.
- `UpdateCountryUseCase` re-popula `cache_key_country(id)` directamente con el nuevo valor.

Si Redis está caído, las invalidaciones fallan silenciosamente — los reads seguirán devolviendo cache stale hasta que expire por TTL. Trade-off aceptado (cache best-effort).

## Schemas — read-optimized

Las schemas de geo_catalog son **distintas** a las de catalog_admin: solo los fields necesarios para el frontend, sin metadata interna (`created_by`, `is_active` cuando se asume true, etc.).

Ejemplos:
- `CountryListItem`: `id`, `iso_alpha2`, `name`, `phone_code`, `currency_code`.
- `LocalityListItem`: `id`, `name`, `latitude`, `longitude`, `locality_type`.
- `NeighborhoodListItem`: `id`, `code`, `name`, `latitude`, `longitude`.
- `NeighborhoodsByLocalityResponse`: `neighborhoods: dict[str, list[NeighborhoodListItem]]` — un dict por locality.

## Boundaries

- **No escribe nada** — writes en [[catalog-service-catalog-admin]].
- **No hace point-in-polygon** — eso vive en `geo_resolution` (ver [[catalog-service-poi-lifecycle]]).
- **No valida tokens** — endpoints son públicos.
- **No expone `geom` ni `h3_cells`** — solo metadata legible para el frontend. Si un consumer necesita el polígono, deberá usar una API específica (no existe hoy).

## Open items

- `/localities/by-admin-division` no tiene cache hoy. Decidir si vale agregarla con `cache_key_localities_by_admin_division(admin_division_id)` o si el patrón de query es lo bastante variado para que no aporte.
- `NeighborhoodInfo` (en geo_resolution) y `NeighborhoodListItem` (en geo_catalog) tienen overlap parcial — evaluar si conviene unificar o mantener separadas por dominio.

## Claims

- Patrón uniforme cache-aside (try cache → DB → repopulate) en los 5 UCs ([get_countries.py:20-44](backend/catalog-service/src/app/services/geo_catalog/use_cases/get_countries.py#L20-L44)).
- `GetNeighborhoodsByLocalityUseCase` batchea cache miss en una sola query a DB, evitando N+1 ([get_neighborhoods_by_locality.py:24-46](backend/catalog-service/src/app/services/geo_catalog/use_cases/get_neighborhoods_by_locality.py#L24-L46)).
- TTL de listas read = `CACHE_TTL_CATALOG_SECONDS` (1 día, settings.py:21).
- `geo_catalog/helpers/cache_keys.py` re-exporta de `shared/helpers/cache_keys.py` para mantener single source of truth de keys ([geo_catalog/helpers/cache_keys.py:1-6](backend/catalog-service/src/app/services/geo_catalog/helpers/cache_keys.py#L1-L6)).
- Llamadas a Redis están en `try/except pass` — caída de Redis degrada a "todo DB" sin romper el read.
- Endpoints de geo_catalog son **públicos** (sin `require_admin` ni auth) ([countries.py:7](backend/catalog-service/src/app/api/routes/countries.py#L7), [localities.py:10](backend/catalog-service/src/app/api/routes/localities.py#L10), [neighborhoods.py:17](backend/catalog-service/src/app/api/routes/neighborhoods.py#L17)).
- `GetLocalitiesUseCase` se reusa para 2 endpoints distintos (`by-country`, `by-admin-division`) inyectando filtros diferentes desde la ruta ([localities.py:13-26](backend/catalog-service/src/app/api/routes/localities.py#L13-L26)).
