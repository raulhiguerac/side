---
title: Dominio catalog_admin (catalog-service)
status: draft
last-verified: 2026-07-18
owners: [catalog-service]
related:
  - "[[catalog-service]]"
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-geo-catalog]]"
  - "[[catalog-service-poi-lifecycle]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../../sources/catalog-service/2026-06-23-overpass-406-and-h3-chicken-egg-fix.md, ../../../sources/catalog-service/2026-07-18-h3-precompute-and-bulk-resolve.md]
---

## TL;DR

Dominio de **writes** del catálogo geográfico. CRUD por entidad (country / admin_division / locality / neighborhood) + bulk uploads (CSV de barrios, GeoJSON de polígonos). Todo protegido por `require_admin`. Cache invalidation explícita después de cada write. Errores SQL mapeados a errores de dominio vía traductor centralizado.

## Public surface

Todo bajo `/v1/admin/*`, protegido globalmente con `Depends(require_admin)` (ver [[catalog-service-architecture]]).

| Método | Path | UC |
|---|---|---|
| POST | `/countries` | `CreateCountryUseCase` |
| PATCH | `/countries/{country_id}` | `UpdateCountryUseCase` |
| POST | `/admin-divisions` | `CreateAdminDivisionUseCase` |
| PATCH | `/admin-divisions/{admin_division_id}` | `UpdateAdminDivisionUseCase` |
| POST | `/localities` | `CreateLocalityUseCase` |
| PATCH | `/localities/{locality_id}` | `UpdateLocalityUseCase` |
| POST | `/neighborhoods` | `CreateNeighborhoodUseCase` |
| PATCH | `/neighborhoods/{neighborhood_id}` | `UpdateNeighborhoodUseCase` |
| POST | `/localities/{locality_id}/neighborhoods/bulk` (CSV/JSON upload) | `BulkCreateNeighborhoodsUseCase` |
| POST | `/localities/{locality_id}/neighborhoods/bulk/geometry` ([[glossary#geojson]] upload) | `BulkEnrichNeighborhoodGeometriesUseCase` |
| POST | `/neighborhoods/{neighborhood_id}/geometry` (single GeoJSON) | `EnrichNeighborhoodGeometryUseCase` |

## Componentes

| Pieza | Archivo |
|---|---|
| UCs CRUD por entidad | `use_cases/{create,update}_{country,admin_division,locality,neighborhood}.py` |
| UCs bulk | `use_cases/bulk_create_neighborhoods.py`, `use_cases/bulk_enrich_neighborhood_geometries.py`, `use_cases/enrich_neighborhood_geometry.py` |
| Ports por entidad | `ports/{country,admin_division,locality,neighborhood}_repository.py`, `ports/unit_of_work.py` |
| Adapters SQL | `adapters/sql_{country,admin_division,locality,neighborhood}_repository.py`, `adapters/sql_unit_of_work.py` |
| Helpers | `helpers/file_parser.py`, `helpers/db_error_translator.py` |
| Schemas | `schemas/{country,admin_division,locality,neighborhood}.py` |

## Patrón de UC estándar (update)

[update_country.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/update_country.py) es representativo:

1. `uow.countries.get_by_id(country_id)` → si no existe, `CountryNotFoundError`.
2. Aplicar `request.model_dump(exclude_unset=True)` con `setattr` — patch semántico.
3. `await uow.commit()` + `await uow.refresh(db_model)`.
4. Si falla: `rollback()` + `raise translate_db_error(exc) from exc` (ver más abajo).
5. **Cache repopulate** (best-effort): `cache_client.set_json(cache_key_country(id), model.model_dump, ttl=CACHE_TTL_ENTITY_SECONDS)` en `try/except pass`.
6. Return `Response.model_validate(db_model)`.

Patrón create es análogo sin el `get_by_id` inicial.

## Bulk uploads — dos UCs, dos archivos, dos formatos

### `BulkCreateNeighborhoodsUseCase` (crear barrios desde CSV/JSON)

Endpoint recibe `UploadFile`. La ruta llama [`NeighborhoodFileParser().parse(file, filename)`](backend/catalog-service/src/app/services/catalog_admin/helpers/file_parser.py) que despacha por extensión:
- `.csv` → `csv.DictReader` → list of dicts.
- `.json` / `.txt` → `json.loads` → list of dicts.
- Otra extensión → `ValueError`.

Flujo del UC ([bulk_create_neighborhoods.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_create_neighborhoods.py)):

1. Mapea cada dict a `Neighborhood(locality_id, code, postal_code, name, search_name=_normalize(name), latitude, longitude, is_active)` con `_normalize` (NFKD + lowercase + strip de tildes).
2. **Happy path**: `uow.neighborhoods.bulk_insert(model_list)` + `commit()`. Devuelve `BulkCreateNeighborhoodsResult(created=N, errors=[])`. **Bug encontrado y corregido 2026-06-23**: `bulk_insert` armaba el `INSERT` con `n.model_dump()`, que serializa `created_at`/`updated_at` como `NULL` explícito (son `server_default`, sin default de Python) — violaba el `NOT NULL` y hacía que el happy path **siempre** fallara, cayendo siempre al fallback fila-por-fila sin que nadie lo notara (el fallback "funcionaba", así que el bug quedaba invisible). Fix: `model_dump(exclude={"created_at", "updated_at"})`.
3. **Fallback row-by-row** si bulk falla:
   - `rollback()`.
   - Por cada neighborhood: `begin_nested()` (savepoint) → `add(neighborhood)` → si falla, `rollback_to_savepoint()` + agrega `neighborhood.name` a `errors`.
   - Al final, `commit()` único si hubo `ok_count > 0`.
4. **Invalida cache**: `cache_client.delete(cache_key_neighborhoods(locality_id))`.
5. Returns `BulkCreateNeighborhoodsResult(created=ok_count, errors=errors)`.

El patrón "intentar bulk, caer a row-by-row con savepoint" es similar al que usa `BatchPrediction` en [[analytics-service-prediction]] — convención del repo para uploads de tamaño variable.

### `BulkEnrichNeighborhoodGeometriesUseCase` (poblar polígonos desde GeoJSON FeatureCollection)

Recibe un `geojson` dict y `name_field: str` (nombre del attribute en `properties` que matchea el nombre del barrio).

Flujo ([bulk_enrich_neighborhood_geometries.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py)):

1. Construye `neighborhood_lookup: dict[str, dict]` — mapa de `_normalize(props[name_field]) → feature`. Dedup por nombre normalizado (primer match gana).
2. `uow.neighborhoods.get_many_by_search_names(locality_id, search_names)` — fetch en una query.
3. Computa `unmatched` (nombres del GeoJSON sin barrio en DB).
4. Construye `updates = [{"id": n.id, "geom": geom_from_geojson(feature['geometry']), "h3_cells": h3_cells_for_geojson(feature['geometry'], resolution=settings.H3_RESOLUTION)} for n in neighborhoods]`. Ambos helpers viven en [`shared/helpers/geometry.py`](backend/catalog-service/src/app/services/shared/helpers/geometry.py).
5. `uow.neighborhoods.bulk_update(updates)` + `commit()`.
6. **Invalida cache**: borra `cache_key_neighborhood(id)` por cada barrio actualizado + `cache_key_neighborhoods(locality_id)`.
7. Returns `BulkEnrichNeighborhoodGeometriesResult(matched, unmatched, updated)`.

Logging detallado para diagnóstico de matching imperfecto (sample de unmatched, conteos por etapa).

**Precompute de `h3_cells` (2026-07-18)**: además de `geom`, este UC ahora calcula la cobertura H3 completa del polígono (`h3_cells_for_geojson` → `h3.geo_to_cells(geojson, resolution)`) y la persiste junto con la geometría — antes `h3_cells` solo se llenaba incrementalmente vía el side-effect de `ResolvePoiUseCase` en `geo_resolution` (ver [[catalog-service-poi-lifecycle]]). `EnrichNeighborhoodGeometryUseCase` ([enrich_neighborhood_geometry.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/enrich_neighborhood_geometry.py)) — la contraparte single-record, para un solo GeoJSON `Polygon`/`MultiPolygon` vía `POST /neighborhoods/{id}/geometry` — hace exactamente lo mismo: setea `db_model.geom` y `db_model.h3_cells` juntos antes del commit.

## Translator de errores SQL → dominio

[`helpers/db_error_translator.py`](backend/catalog-service/src/app/services/catalog_admin/helpers/db_error_translator.py) centraliza el mapeo:

- **`IntegrityError`** → parsea el mensaje de PG con regex (`constraint "..."` y `Key (field)=(value)`) → matchea contra `_CONSTRAINT_MAP` (constraint name → factory de error de dominio):

| Constraint PG | Error de dominio |
|---|---|
| `countries_iso_alpha2_key` | `CountryConflictError(field, value)` |
| `countries_iso_alpha3_key` | `CountryConflictError` |
| `countries_iso_numeric_key` | `CountryConflictError` |
| `uq_admin_div_country_code` | `AdminDivisionConflictError` |
| `uq_locality_country_code` | `LocalityConflictError` |
| `uq_neighborhood_locality_code` | `NeighborhoodConflictError` |

- **`OperationalError`** → `CatalogAdminDbUnavailableError(cause=exc)`.
- Otro: se devuelve la excepción original sin envolverla.

Uso en UCs:
```python
except Exception as exc:
    await self.uow.rollback()
    raise translate_db_error(exc) from exc
```

**Trade-off**: el regex sobre el message string es frágil — si PG cambia el formato del error, el matching rompe silenciosamente y se devuelve el `IntegrityError` crudo. Aceptable hoy, vigilar en upgrades de PG.

## Cache invalidation pattern

Para cada write, el UC borra (o repopula) las keys de Redis cuyo dato fue afectado. Constructores de keys en [`shared/helpers/cache_keys.py`](backend/catalog-service/src/app/services/shared/helpers/cache_keys.py):

- `cache_key_countries()` — lista de países activos
- `cache_key_country(country_id)` — entidad individual
- `cache_key_localities(country_id)` y `cache_key_locality(locality_id)`
- `cache_key_neighborhoods(locality_id)` y `cache_key_neighborhood(neighborhood_id)`

Llamadas a `cache_client.*` siempre wrapeadas en `try/except pass` — cache best-effort.

## Boundaries

- **No expone reads** — eso vive en [[catalog-service-geo-catalog]].
- **No hace geocoding** — eso vive en `geo_resolution`.
- **No valida JWT** — solo lo consume vía `require_admin` que valida internamente con JWKS.
- **No parsea polígonos** — delega a `geom_from_geojson` de `shared/helpers/geometry.py`.

## Open items

- Trasladar `_normalize` (NFKD+lower+strip) a `shared/helpers/text.py` — hoy se duplica en `bulk_create_neighborhoods` y `bulk_enrich_neighborhood_geometries` con el mismo body.
- Validar el GeoJSON antes de aplicar `geom_from_geojson` (hoy si el `geometry` es malformado, falla en el bulk_update y se pierde el batch).
- Robustecer el regex del db_error_translator o switch a códigos numéricos de PG (`SQLSTATE` 23505 para unique violation).

## Claims

- Todo `/admin/*` está protegido vía `Depends(require_admin)` en el `APIRouter` ([admin.py:74](backend/catalog-service/src/app/api/routes/admin.py#L74)).
- `BulkCreateNeighborhoodsUseCase` intenta bulk insert primero y cae a row-by-row con savepoints (`begin_nested`/`rollback_to_savepoint`) si el bulk falla ([bulk_create_neighborhoods.py:45-83](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_create_neighborhoods.py#L45-L83)).
- `SqlNeighborhoodAdminRepository.bulk_insert` excluye `created_at`/`updated_at` del `model_dump()` antes del `INSERT` — sin esto, el `NOT NULL` de esas columnas (`server_default`, sin default Python) rechazaba el insert y el happy path nunca corría ([sql_neighborhood_repository.py:33-37](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L33-L37)). Corregido 2026-06-23.
- `BulkEnrichNeighborhoodGeometriesUseCase` matchea features de GeoJSON con barrios por `search_name` normalizado (NFKD + lowercase + strip) y reporta `unmatched` ([bulk_enrich_neighborhood_geometries.py:37-99](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py#L37-L99)).
- `BulkEnrichNeighborhoodGeometriesUseCase` y `EnrichNeighborhoodGeometryUseCase` precomputan `h3_cells` (cobertura completa del polígono) junto con `geom`, vía `h3_cells_for_geojson(geometry, resolution=settings.H3_RESOLUTION)` ([bulk_enrich_neighborhood_geometries.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/bulk_enrich_neighborhood_geometries.py), [enrich_neighborhood_geometry.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/enrich_neighborhood_geometry.py)). Agregado 2026-07-18.
- `db_error_translator.translate_db_error` mapea constraints PG → errores de dominio vía regex sobre el message string ([db_error_translator.py:25-62](backend/catalog-service/src/app/services/catalog_admin/helpers/db_error_translator.py#L25-L62)).
- Las llamadas a `cache_client` están envueltas en `try/except pass` — cache es best-effort, su caída no rompe writes ([update_country.py:42-48](backend/catalog-service/src/app/services/catalog_admin/use_cases/update_country.py#L42-L48)).
- El parser de archivos acepta `.csv`, `.json`, `.txt`; cualquier otra extensión lanza `ValueError` ([file_parser.py:8-14](backend/catalog-service/src/app/services/catalog_admin/helpers/file_parser.py#L8-L14)).
- `_normalize` (NFKD+lowercase+strip) está duplicada idéntica en `bulk_create_neighborhoods` y `bulk_enrich_neighborhood_geometries`.
