---
title: Dominio catalog_admin (catalog-service)
status: stable
last-verified: 2026-10-16
owners: [catalog-service]
related:
  - "[[catalog-service]]"
  - "[[catalog-service-architecture]]"
  - "[[catalog-service-geo-catalog]]"
  - "[[catalog-service-poi-lifecycle]]"
  - "[[frontend-admin-panel]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md, ../../../sources/catalog-service/2026-06-23-overpass-406-and-h3-chicken-egg-fix.md, ../../../sources/catalog-service/2026-07-18-h3-precompute-and-bulk-resolve.md, ../../../sources/catalog-service/2026-10-04-admin-neighborhoods-read-endpoints.md, ../../../sources/frontend/2026-09-28-admin-catalog-geometry-design.md, ../../../sources/catalog-service/2026-10-10-admin-localities-list-endpoint.md, ../../../sources/catalog-service/2026-10-14-admin-pagination-standard.md, ../../../sources/catalog-service/2026-10-14-admin-divisions-countries-list-endpoints.md, ../../../sources/frontend/2026-10-16-admin-localities-tab-and-shared-pieces.md]
---

## TL;DR

Dominio admin del catálogo geográfico: **writes** (CRUD por entidad + bulk uploads de CSV de barrios y GeoJSON de polígonos, con cache invalidation explícita) y **reads admin** para el panel: barrios (listado paginado con silueta, detalle con geometría, vecinos por bbox) y listados paginados con inactivos de localidades, divisiones y países. Todo protegido por `require_admin`; las lecturas admin van directo a la DB, sin cache. Errores SQL mapeados a errores de dominio vía traductor centralizado.

## Public surface

Todo bajo `/v1/admin/*`, protegido globalmente con `Depends(require_admin)` (ver [[catalog-service-architecture]]).

| Método | Path | UC |
|---|---|---|
| GET | `/neighborhoods` (paginado + filtros) | `ListNeighborhoodsUseCase` |
| GET | `/neighborhoods/geometries?neighborhood_id&bbox` | `ListNeighborhoodGeometriesUseCase` |
| GET | `/neighborhoods/{neighborhood_id}` | `GetNeighborhoodDetailUseCase` |
| GET | `/localities` (paginado + filtros) | `ListLocalitiesUseCase` |
| GET | `/admin-divisions` (paginado + filtros) | `ListAdminDivisionsUseCase` |
| GET | `/countries` (paginado + filtros) | `ListCountriesUseCase` |
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
| UCs CRUD por entidad | `use_cases/{country,admin_division,locality,neighborhood}/{create,update}.py` |
| UCs bulk | `use_cases/neighborhood/{bulk_create,bulk_enrich_geometries,enrich_geometry}.py` |
| UCs reads admin | `use_cases/neighborhood/{list_all,get_detail,list_geometries}.py` |
| Rutas | `api/routes/admin/{countries,admin_divisions,localities,neighborhoods}.py`; el `__init__.py` monta el prefix `/admin` y `require_admin` |
| DI | `api/deps/catalog_admin/{countries,admin_divisions,localities,neighborhoods}.py` + `uow.py` (`get_uow`) |
| Ports por entidad | `ports/{country,admin_division,locality,neighborhood}_repository.py`, `ports/unit_of_work.py` |
| Adapters SQL | `adapters/sql_{country,admin_division,locality,neighborhood}_repository.py`, `adapters/sql_unit_of_work.py` |
| Helpers | `helpers/file_parser.py`, `helpers/db_error_translator.py` |
| Schemas | `schemas/{country,admin_division,locality,neighborhood}.py` |

## Patrón de UC estándar (update)

[country/update.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/country/update.py) es representativo:

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

Flujo del UC ([neighborhood/bulk_create.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/bulk_create.py)):

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

Flujo ([neighborhood/bulk_enrich_geometries.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/bulk_enrich_geometries.py)):

1. Construye `neighborhood_lookup: dict[str, dict]` — mapa de `_normalize(props[name_field]) → feature`. Dedup por nombre normalizado (primer match gana).
2. `uow.neighborhoods.get_many_by_search_names(locality_id, search_names)` — fetch en una query.
3. Computa `unmatched` (nombres del GeoJSON sin barrio en DB).
4. Construye `updates = [{"id": n.id, "geom": geom_from_geojson(feature['geometry']), "h3_cells": h3_cells_for_geojson(feature['geometry'], resolution=settings.H3_RESOLUTION)} for n in neighborhoods]`. Ambos helpers viven en [`shared/helpers/geometry.py`](backend/catalog-service/src/app/services/shared/helpers/geometry.py).
5. `uow.neighborhoods.bulk_update(updates)` + `commit()`.
6. **Invalida cache**: borra `cache_key_neighborhood(id)` por cada barrio actualizado + `cache_key_neighborhoods(locality_id)`.
7. Returns `BulkEnrichNeighborhoodGeometriesResult(matched, unmatched, updated)`.

Logging detallado para diagnóstico de matching imperfecto (sample de unmatched, conteos por etapa).

**Precompute de `h3_cells` (2026-07-18)**: además de `geom`, este UC ahora calcula la cobertura H3 completa del polígono (`h3_cells_for_geojson` → `h3.geo_to_cells(geojson, resolution)`) y la persiste junto con la geometría — antes `h3_cells` solo se llenaba incrementalmente vía el side-effect de `ResolvePoiUseCase` en `geo_resolution` (ver [[catalog-service-poi-lifecycle]]). `EnrichNeighborhoodGeometryUseCase` ([neighborhood/enrich_geometry.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/enrich_geometry.py)) — la contraparte single-record, para un solo GeoJSON `Polygon`/`MultiPolygon` vía `POST /neighborhoods/{id}/geometry` — hace exactamente lo mismo: setea `db_model.geom` y `db_model.h3_cells` juntos antes del commit.

## Reads admin de barrios

Alimentan la tab de barrios del panel admin ([[frontend-admin-panel]]). A diferencia de [[catalog-service-geo-catalog]], incluyen inactivos y **no pasan por cache**: el admin escribe y mira la misma pantalla para comprobar el resultado. Las columnas calculadas (silueta, bbox, GeoJSON, área) salen de PostGIS y el adapter arma los schemas con `model_validate(row)`; se seleccionan columnas sueltas para no cargar `geom` ni `h3_cells` completos.

**Listado — `GET /neighborhoods`.** Paginado por offset con el contrato compartido (ver [Paginación de los listados admin](#paginación-de-los-listados-admin)). Request `ListNeighborhoodsAdminRequest(PageRequest)`: `page`, `page_size` + `locality_id`, `is_active`, `has_geometry`, `search_term`. Respuesta `NeighborhoodAdminPage(Page[NeighborhoodAdminListItem])`: los campos de `Page` + `coverage`, armada con `NeighborhoodAdminPage.build(..., coverage=coverage)`. Los nombres difieren a propósito de `total/page/page_size` de properties.
- Cada item trae `has_geometry`, `svg_path` (`ST_AsSVG` relativo, 5 decimales, sobre la geometría simplificada) y `bbox` `(min_lon, min_lat, max_lon, max_lat)` para el `viewBox`. `ST_AsSVG` invierte la Y, así que el `viewBox` es `min_lon, -max_lat, ancho, alto`.
- `get_all`, `count_all` y `get_coverage` comparten `_apply_filters`, así que `total_items` siempre cuadra con la lista.
- `coverage` (`with_geometry` / `total`) ignora `has_geometry`; con ese filtro la barra marcaría siempre 0 % o 100 %.
- `search_term` se normaliza igual que `search_name` y filtra con `LIKE` + `autoescape`, sin índice (~1,2k filas y debounce en el front; si crece, `pg_trgm`).
- Descartado: calcular coverage en el front por página (engañoso) y cachear los conteos por checksum del request (~1 ms en Postgres contra invalidar en cinco UCs de escritura).

**Detalle — `GET /neighborhoods/{neighborhood_id}`.** `NeighborhoodAdminDetail` = `NeighborhoodAdminResponse` + `geometry` (GeoJSON) + `area_m2`. El área se calcula sobre la geometría original casteada a `geography`; sobre `geometry` 4326 saldría en grados². Si no existe → 404 `NEIGHBORHOOD_ADMIN_NOT_FOUND`. `get_by_id` se mantiene para las escrituras, que necesitan el modelo ORM.

**Vecinos — `GET /neighborhoods/geometries`.** El front manda el bbox visible del mapa (`map.getBounds()`) y el `neighborhood_id` a excluir. `ST_Intersects` contra el envelope (usa el índice GiST `ix_neighborhood_geom`), recorte con `ST_ClipByBox2D` y simplificación. Devuelve `list[{id, name, geometry}]`, no un FeatureCollection. La ruta se declara antes de `/neighborhoods/{neighborhood_id}`; si no, FastAPI toma "geometries" como id.
- El bbox se valida en el schema: rangos con `ge`/`le`, `min < max` y lado máximo `0.135°` (~15 km). En la ruta va como `Annotated[..., Query()]` porque con `Depends()` FastAPI trata la `tuple` como body. Llega repetido: `?bbox=a&bbox=b&bbox=c&bbox=d`.

**Simplificación.** Tolerancia `0.00001°` (~1,1 m) para silueta, detalle y vecinos, medida sobre los 1202 barrios:

| | sin simplificar | ~1,1 m (elegida) | ~5,5 m |
|---|---|---|---|
| GeoJSON promedio / máx. | 9,2 KB / 247 KB | 1,7 KB / 46 KB | 0,8 KB / 18 KB |
| SVG promedio | 4,6 KB | 1,3 KB | — |
| Cambio máximo de área | — | 1,1 % | 25 % |

Al simplificar, los `MULTIPOLYGON` de una sola parte vuelven como `Polygon` (1196 de 1202); el front tiene que aceptar ambos tipos.

## Paginación de los listados admin

Los `GET` de listado admin comparten un contrato único definido en [`app/schemas/pagination.py`](backend/catalog-service/src/app/schemas/pagination.py), junto a `StrictBase` y no dentro de `catalog_admin` porque es transversal. El back calcula todo lo que el front necesita para paginar.

- **`PageRequest`**: `page` (≥1, def. 1) y `page_size` (1–100, def. 20). Expone `offset = (page - 1) * page_size` como **propiedad**, no como campo: no aparece como query param y los repos usan `req.offset` sin repetir la fórmula.
- **`Page[T]`** (genérico de Pydantic): `items`, `total_items`, `total_pages`, `current_page`, `items_per_page`. `Page.build(items=, total_items=, req=, **extra)` calcula `total_pages` y deja pasar campos propios de cada listado (como `coverage`).
- **Se hereda, no se anida.** Cada request de listado extiende `PageRequest` y suma solo sus filtros; cada página extiende `Page[Item]`. Un campo anidado (`pagination: PageRequest`) no sirve: `Depends()` no aplana modelos anidados a query params. Heredando, el OpenAPI muestra los params planos.
- Solo catalog-service. properties-service usa otro formato (`total`, `page`, `page_size`); unificarlo rompería moderación, promociones e imports del front y queda como pregunta abierta.

## Reads admin de localidades, divisiones y países

Alimentan las tabs de localidades, divisiones y países del panel ([[frontend-admin-panel]]). Mismo criterio que barrios: incluyen inactivos y va directo a la DB, sin cache. Los GET públicos de [[catalog-service-geo-catalog]] no se parametrizan con un `include_inactive`: van cacheados y son públicos, así que el admin tiene su propio read path.

**Listado — `GET /localities`.** Request `GetAllLocalitiesRequest(PageRequest)` (en la ruta como `Depends()`): `page`, `page_size` + `country_id`, `admin_division_id`, `is_active` opcionales. Respuesta `GetAllLocalitiesPage(Page[GetAllLocalitiesResponse])`, armada con `build`: mismos metadatos que barrios, sin `coverage`. Cada item trae `id`, `country_id`, `admin_division_id`, `code`, `name`, `local_name`, `locality_type`, `point {latitude, longitude}`, `timezone`, `is_active`, `is_capital`: todo lo editable por el `PATCH` más los ids para la cascada país → división del formulario (los campos se sumaron el 2026-10-14; son columnas que `Locality` ya tenía).
- Hasta 2026-10-14 paginaba con `offset` y devolvía solo `total_items`; se unificó con barrios para que el front use un solo tipo de página.
- `get_all` (con `order_by(name, id)`, `req.offset`, `limit`) y `count_all` comparten `_apply_filters`, igual que barrios. `is_active` se compara con `is not None` para que el filtro `false` funcione.
- `Locality` guarda `latitude`/`longitude` como columnas planas, así que `model_validate` no arma el `point` anidado: el UC mapea con una list comprehension. El `point` queda listo para un mapa.
- El `try/except → translate_db_error` envuelve solo las llamadas al repo; el mapeo queda afuera para que un bug de mapeo no salga como error de DB.

**Cache de crear y editar localidad.** Los dos UCs borran bien las listas públicas (`cache_key_localities` y `cache_key_localities_by_admin_division`), pero en `cache_key_locality(id)` hacen `set_json` del modelo completo. `GetLocalityByIdUseCase` lee esa key como `LocalityListItem`, que es `extra="forbid"` y exige `admin_division`: la validación falla, cae al `except` y va a la DB, que filtra `is_active`. Hoy invalida de casualidad; el fix es un `delete` ([[open-items]]).

**Listado — `GET /admin-divisions`.** `GetAllAdminDivisionsRequest(PageRequest)` con `country_id` e `is_active` opcionales. Responde `GetAllAdminDivisionsPage(Page[AdminDivisionResponse])`: reusa el schema del POST/PATCH porque ya trae todos los campos editables (`country_id`, `code`, `iso_code`, `name`, `type_name`, `is_active`). Desbloquea crear una localidad desde el panel, que exige `admin_division_id`.

**Listado — `GET /countries`.** `GetAllCountriesRequest(PageRequest)` con `is_active` e `is_supported` opcionales. Responde `GetAllCountriesPage(Page[GetAllCountriesResponse])`, con un item propio que trae todos los campos del modelo (`iso_alpha2/3`, `iso_numeric`, `official_name`, `native_name`, `phone_code`, `currency_code`, `default_locale`, `default_timezone`, flags). No extiende `CountryResponse` para no cambiar la respuesta de POST/PATCH ni sus tests.

Los dos copian el patrón de localidades: `_apply_filters` compartido por `get_all`/`count_all`, `order_by(name, id)`, `req.offset`/`limit`, `translate_db_error` solo sobre el repo, `model_validate` del ORM (no hay campos anidados que armar) y `Page.build`. Probados contra el Postgres de dev el 2026-10-14 con un país y una división, así que la paginación con volumen no se ejercitó contra la base.

**Los cuatro listados son casi iguales.** Es la ceremonia hexagonal sobre una lectura pura. Lo único que amerita abstraerse es el repo (`get_all`/`count_all` genérico sobre modelo + filtros + orden), y solo para localidades, divisiones y países: el `get_all` de barrios selecciona columnas calculadas (`svg_path`, `bbox`), no el modelo. Los UCs divergen (barrios hace 3 queries y suma `coverage`; localidades arma `point`) y deps/rutas son el idiom de FastAPI. Sin decidir.

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

- **Reads públicos no** — esos viven en [[catalog-service-geo-catalog]] (cacheados, solo activos). Aquí solo están los reads admin (barrios, localidades, divisiones y países).
- **No hace geocoding** — eso vive en `geo_resolution`.
- **No valida JWT** — solo lo consume vía `require_admin` que valida internamente con JWKS.
- **No parsea polígonos** — delega a `geom_from_geojson` de `shared/helpers/geometry.py`.

## Open items

- Trasladar la normalización de `search_name` (NFKD+lower+strip) a `shared/helpers/text.py` — hoy está copiada en 8 archivos (UCs de barrio y localidad, bulks, el adapter de barrios y `geo_resolution/.../overpass.py`).
- ¿Repo base genérico para los listados de localidades, divisiones y países (~30 líneas menos, un solo sitio si cambia la paginación) o copia explícita? Barrios quedaría afuera.
- ¿El select de división al crear una localidad debe ofrecer divisiones inactivas?
- `total_pages` sale 0 sin resultados; sin `locality_id`, `coverage` mide todo el catálogo filtrado; ¿bbox con comas en vez de repetido? — decisiones abiertas.
- Hay barrios con nombre repetido ("El Bagazal", "El Refugio"): sin confirmar si son homónimos o duplicados de origen.
- Las queries del adapter (`_apply_filters`, coverage, `get_geometries`) no tienen tests de integración con PostGIS.
- Validar el GeoJSON antes de aplicar `geom_from_geojson` (hoy si el `geometry` es malformado, falla en el bulk_update y se pierde el batch).
- Robustecer el regex del db_error_translator o switch a códigos numéricos de PG (`SQLSTATE` 23505 para unique violation).

## Claims

- Todo `/admin/*` está protegido vía `Depends(require_admin)` en el `APIRouter` que monta los cuatro subrouters por entidad ([routes/admin/__init__.py:6-10](backend/catalog-service/src/app/api/routes/admin/__init__.py#L6-L10)).
- `GET /admin/neighborhoods/geometries` se declara antes que `GET /admin/neighborhoods/{neighborhood_id}` ([routes/admin/neighborhoods.py:71-79](backend/catalog-service/src/app/api/routes/admin/neighborhoods.py#L71-L79)).
- `get_all`, `count_all` y `get_coverage` aplican los mismos filtros vía `_apply_filters` ([sql_neighborhood_repository.py:44-56](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L44-L56)).
- `get_coverage` aplica los filtros con `has_geometry` en `None` ([sql_neighborhood_repository.py:95](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L95)).
- `search_term` filtra `search_name` con `contains(..., autoescape=True)` tras normalizarlo ([sql_neighborhood_repository.py:56](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L56)).
- La silueta del listado usa `ST_AsSVG(ST_SimplifyPreserveTopology(geom, 0.00001), 1, 5)` ([sql_neighborhood_repository.py:41](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L41), [:77](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L77)).
- `area_m2` del detalle se calcula con `ST_Area` sobre la geometría original casteada a `Geography` ([sql_neighborhood_repository.py:116](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L116)).
- `get_geometries` filtra con `ST_Intersects` y recorta con `ST_ClipByBox2D` antes de simplificar ([sql_neighborhood_repository.py:121-130](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L121-L130)).
- `ListNeighborhoodGeometriesRequest` rechaza un bbox con `min >= max` o con un lado mayor a `0.135°` ([schemas/neighborhood.py:9](backend/catalog-service/src/app/services/catalog_admin/schemas/neighborhood.py#L9), [:75-86](backend/catalog-service/src/app/services/catalog_admin/schemas/neighborhood.py#L75-L86)).
- `PageRequest` expone `offset` como propiedad `(page - 1) * page_size`, no como campo ([schemas/pagination.py:12-18](backend/catalog-service/src/app/schemas/pagination.py#L12-L18)).
- `Page.build` calcula `total_pages` como `ceil(total_items / page_size)` y reenvía campos extra al constructor ([schemas/pagination.py:28-37](backend/catalog-service/src/app/schemas/pagination.py#L28-L37)).
- `ListNeighborhoodsAdminRequest` y `GetAllLocalitiesRequest` heredan de `PageRequest`; `NeighborhoodAdminPage` y `GetAllLocalitiesPage` heredan de `Page[...]` ([schemas/neighborhood.py:48](backend/catalog-service/src/app/services/catalog_admin/schemas/neighborhood.py#L48), [:71](backend/catalog-service/src/app/services/catalog_admin/schemas/neighborhood.py#L71), [schemas/locality.py:47](backend/catalog-service/src/app/services/catalog_admin/schemas/locality.py#L47), [:68](backend/catalog-service/src/app/services/catalog_admin/schemas/locality.py#L68)).
- Los use cases de listado de barrios y localidades arman la respuesta con `Page.build` ([neighborhood/list_all.py:25](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/list_all.py#L25), [locality/list_all.py:39](backend/catalog-service/src/app/services/catalog_admin/use_cases/locality/list_all.py#L39)).
- `GetNeighborhoodDetailUseCase` lanza `NeighborhoodAdminNotFoundError` si el repo devuelve `None` ([get_detail.py:25](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/get_detail.py#L25)).
- Los providers de los tres reads admin no inyectan `cache_client` ([deps/catalog_admin/neighborhoods.py:33-48](backend/catalog-service/src/app/api/deps/catalog_admin/neighborhoods.py#L33-L48)).
- `_apply_filters` de localidades compara `is_active` con `is not None` ([sql_locality_repository.py:16](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_locality_repository.py#L16)).
- `get_all` de localidades ordena por `name, id` y pagina con `req.offset`/`limit`; `count_all` aplica los mismos filtros sobre `func.count()` ([sql_locality_repository.py:25-36](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_locality_repository.py#L25-L36)).
- `ListLocalitiesUseCase` arma `point` desde `latitude`/`longitude` del modelo ([locality/list_all.py:32](backend/catalog-service/src/app/services/catalog_admin/use_cases/locality/list_all.py#L32)).
- El provider del listado de localidades no inyecta `cache_client` ([deps/catalog_admin/localities.py:12-15](backend/catalog-service/src/app/api/deps/catalog_admin/localities.py#L12-L15)).
- `GetAllLocalitiesResponse` incluye `country_id`, `admin_division_id`, `local_name` y `timezone` ([schemas/locality.py:58-69](backend/catalog-service/src/app/services/catalog_admin/schemas/locality.py#L58-L69)).
- `GetAllAdminDivisionsRequest` y `GetAllCountriesRequest` heredan de `PageRequest`; la página de divisiones reusa `AdminDivisionResponse` como item ([schemas/admin_division.py:33-39](backend/catalog-service/src/app/services/catalog_admin/schemas/admin_division.py#L33-L39), [schemas/country.py:46](backend/catalog-service/src/app/services/catalog_admin/schemas/country.py#L46)).
- `GetAllCountriesResponse` es un schema propio, distinto de `CountryResponse` ([schemas/country.py:51-64](backend/catalog-service/src/app/services/catalog_admin/schemas/country.py#L51-L64)).
- El repo de divisiones filtra por `country_id` e `is_active`; el de países por `is_active` e `is_supported`, ambos con `is not None` para los booleanos ([sql_admin_division_repository.py:16](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_admin_division_repository.py#L16), [sql_country_repository.py:12](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_country_repository.py#L12)).
- `ListAdminDivisionsUseCase` y `ListCountriesUseCase` mapean con `model_validate` y arman la respuesta con `Page.build` ([admin_division/list_all.py:25-26](backend/catalog-service/src/app/services/catalog_admin/use_cases/admin_division/list_all.py#L25-L26), [country/list_all.py:25-26](backend/catalog-service/src/app/services/catalog_admin/use_cases/country/list_all.py#L25-L26)).
- Los providers de los listados de divisiones y países no inyectan `cache_client` ([deps/catalog_admin/admin_divisions.py:18](backend/catalog-service/src/app/api/deps/catalog_admin/admin_divisions.py#L18), [deps/catalog_admin/countries.py:12](backend/catalog-service/src/app/api/deps/catalog_admin/countries.py#L12)).
- `BulkCreateNeighborhoodsUseCase` intenta bulk insert primero y cae a row-by-row con savepoints (`begin_nested`/`rollback_to_savepoint`) si el bulk falla ([neighborhood/bulk_create.py:45-83](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/bulk_create.py#L45-L83)).
- `SqlNeighborhoodAdminRepository.bulk_insert` excluye `created_at`/`updated_at` del `model_dump()` antes del `INSERT` — sin esto, el `NOT NULL` de esas columnas (`server_default`, sin default Python) rechazaba el insert y el happy path nunca corría ([sql_neighborhood_repository.py:33-37](backend/catalog-service/src/app/services/catalog_admin/adapters/sql_neighborhood_repository.py#L33-L37)). Corregido 2026-06-23.
- `BulkEnrichNeighborhoodGeometriesUseCase` matchea features de GeoJSON con barrios por `search_name` normalizado (NFKD + lowercase + strip) y reporta `unmatched` ([neighborhood/bulk_enrich_geometries.py:37-99](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/bulk_enrich_geometries.py#L37-L99)).
- `BulkEnrichNeighborhoodGeometriesUseCase` y `EnrichNeighborhoodGeometryUseCase` precomputan `h3_cells` (cobertura completa del polígono) junto con `geom`, vía `h3_cells_for_geojson(geometry, resolution=settings.H3_RESOLUTION)` ([neighborhood/bulk_enrich_geometries.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/bulk_enrich_geometries.py), [neighborhood/enrich_geometry.py](backend/catalog-service/src/app/services/catalog_admin/use_cases/neighborhood/enrich_geometry.py)). Agregado 2026-07-18.
- `db_error_translator.translate_db_error` mapea constraints PG → errores de dominio vía regex sobre el message string ([db_error_translator.py:25-62](backend/catalog-service/src/app/services/catalog_admin/helpers/db_error_translator.py#L25-L62)).
- Las llamadas a `cache_client` están envueltas en `try/except pass` — cache es best-effort, su caída no rompe writes ([country/update.py:42-48](backend/catalog-service/src/app/services/catalog_admin/use_cases/country/update.py#L42-L48)).
- El parser de archivos acepta `.csv`, `.json`, `.txt`; cualquier otra extensión lanza `ValueError` ([file_parser.py:8-14](backend/catalog-service/src/app/services/catalog_admin/helpers/file_parser.py#L8-L14)).
- La normalización NFKD+lowercase+strip de `search_name` está copiada en `neighborhood/bulk_create.py`, `neighborhood/bulk_enrich_geometries.py`, `neighborhood/create.py`, `neighborhood/update.py`, `locality/create.py`, `locality/update.py`, `sql_neighborhood_repository.py` y `geo_resolution/adapters/poi/overpass.py`.
- `NeighborhoodAdminResponse` devuelve el centroide (`latitude`/`longitude`) pero no `geom`; la geometría solo sale en `NeighborhoodAdminDetail` ([neighborhood.py:32-40](backend/catalog-service/src/app/services/catalog_admin/schemas/neighborhood.py#L32-L40)).
- `UpdateLocalityUseCase` y `CreateLocalityUseCase` hacen `set_json` de `model_dump()` del modelo en `cache_key_locality(id)`, en el mismo `try` que los `delete` de las listas ([locality/update.py:52](backend/catalog-service/src/app/services/catalog_admin/use_cases/locality/update.py#L52), [locality/create.py:48](backend/catalog-service/src/app/services/catalog_admin/use_cases/locality/create.py#L48)).
