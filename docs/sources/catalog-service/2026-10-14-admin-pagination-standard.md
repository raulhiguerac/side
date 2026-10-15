---
title: Paginación estándar de los GET admin de catalog (PageRequest + Page[T])
captured-from: conversation
captured-on: 2026-10-14
participants: [raul, claude]
---

## Context
Al revisar qué endpoints faltan para terminar el panel admin de catálogo, se vio que localidades paginaba con `offset` + `{items, total_items}` y barrios con `page` + metadatos completos, mientras el front solo tiene `PageParams { page, page_size }`. Se decidió que el back calcule todo lo que sale hacia el front y estandarizar los listados admin de catalog-service (rama `feat/catalog-admin-list-localities`).

## Key conclusions
- Estado de endpoints: barrios completo (listado, detalle, vecinos, PATCH, geometría, bulk); localidades ya tiene `GET /admin/localities`; **faltan `GET /admin/admin-divisions` y `GET /admin/countries`** — sus `list_all.py` son stubs vacíos y los ports no tienen `get_all`/`count_all`. Divisiones bloquea crear localidad (`admin_division_id` obligatorio) y el filtro por división.
- Nuevo módulo compartido `app/schemas/pagination.py` (junto a `StrictBase`, no dentro de `catalog_admin`, por ser transversal):
  - `PageRequest`: `page` (≥1, def. 1), `page_size` (1–100, def. 20) y una **propiedad** `offset = (page - 1) * page_size`; al no ser campo no aparece como query param y los repos usan `req.offset`.
  - `Page[T]` (genérico Pydantic): `items`, `total_items`, `total_pages`, `current_page`, `items_per_page`; `build(items=, total_items=, req=, **extra)` calcula `total_pages = ceil(total_items / page_size)` (0 si no hay filas) y `extra` admite campos propios como `coverage`.
- Se **hereda, no se anida**: cada request de listado extiende `PageRequest` y agrega solo sus filtros. Un campo anidado (`pagination: PageRequest`) rompe `Depends()`, que no aplana modelos anidados a query params. Verificado en el OpenAPI: los params salen planos.
- `GetAllLocalitiesRequest(PageRequest)` reemplaza `offset` por `page`; `GetAllLocalitiesPage(Page[GetAllLocalitiesResponse])`. `ListNeighborhoodsAdminRequest(PageRequest)`; `NeighborhoodAdminPage(Page[NeighborhoodAdminListItem])` + `coverage` — su JSON no cambió, el front de barrios no se entera.
- Ambos use cases (`locality/list_all.py`, `neighborhood/list_all.py`) arman la respuesta con `.build(...)`; el repo de localidades no se tocó (`filters.offset` pasa a ser la propiedad).
- `GetLocalityByIdRequest` se borró: heredaba filtros y paginación del listado y no tenía usos.
- Nuevo test unitario `tests/unit/services/CatalogAdmin/use_cases/locality/test_list_all.py` (espejo del de barrios + offset derivado y validación de paginación). `pytest tests/unit`: 123 pasan, 7 fallan (los preexistentes de GeoCatalog/GeoResolution).
- Alcance: **solo catalog-service**. properties-service usa un tercer formato (`{items, total, page, page_size}` en `AdminPropertiesPage`, `AdminPromotionsPage`, `AdminBulkJobsPage`) y no se toca; cambiarlo rompería moderación, promociones e imports del front.

## Open questions
- Si properties-service debe migrar al mismo formato (implica PR conjunto back + front de sus tres pestañas).

## Next steps
- `GET /admin/admin-divisions` y `GET /admin/countries` nacen heredando `PageRequest` y devolviendo `Page[T]`.
- El listado de localidades aún no trae `country_id`, `admin_division_id`, `local_name`, `timezone` para prellenar el editar; `CountryResponse` tampoco trae `official_name`, `native_name`, `default_locale`, `iso_numeric`.
- En el front, un `AdminPage<T>` genérico en `types/admin/catalog.ts` para las tres pestañas nuevas.
