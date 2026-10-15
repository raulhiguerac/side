---
title: GET admin de divisiones y países, y campos completos en el listado de localidades
captured-from: conversation
captured-on: 2026-10-14
participants: [raul, claude]
---

## Context
Tras unificar la paginación admin (`PageRequest` + `Page[T]`, ver `2026-10-14-admin-pagination-standard.md`), faltaban en el back los listados de divisiones y países y los campos para prellenar el editar de localidades. Con esto el back de lectura del admin de catálogo queda completo (rama `feat/catalog-admin-list-localities`).

## Key conclusions
- `GetAllLocalitiesResponse` suma `country_id`, `admin_division_id`, `local_name` (`str | None`) y `timezone`; son columnas que `Locality` ya tenía, sin migración. Ahora el item trae todo lo editable por el `PATCH` más los ids para la cascada país → división.
- **`GET /admin/admin-divisions`**: `GetAllAdminDivisionsRequest(PageRequest)` con `country_id`, `is_active`; responde `GetAllAdminDivisionsPage(Page[AdminDivisionResponse])` — reusa `AdminDivisionResponse` porque ya trae todos los campos editables.
- **`GET /admin/countries`**: `GetAllCountriesRequest(PageRequest)` con `is_active`, `is_supported`; responde `GetAllCountriesPage(Page[GetAllCountriesResponse])`. Item propio con todos los campos (`iso_numeric`, `official_name`, `native_name`, `default_locale`, …) en vez de extender `CountryResponse`, para no cambiar la respuesta de POST/PATCH ni sus tests.
- Ambos siguen el patrón de localidades: port con `get_all`/`count_all`, adapter con `_apply_filters` compartido, `order_by(name, id)`, `req.offset`/`limit`; UC con `try → translate_db_error` solo sobre el repo y `Page.build`; provider sin `cache_client`; ruta con `Depends()`.
- Verificado: tests unitarios nuevos (`admin_division/test_list_all.py`, `country/test_list_all.py`; 133 pasan, 7 rojos preexistentes), los UCs corridos con los repos SQL contra el Postgres de dev (1 país, 1 división; filtros y página fuera de rango correctos) y el OpenAPI con params planos.
- Los cuatro listados quedan casi idénticos por la ceremonia hexagonal. Análisis: solo el repo amerita abstraerse (`get_all`/`count_all` genérico sobre modelo + filtros + orden); `_apply_filters` es lo que varía, los UCs divergen (barrios: 3 queries + `coverage`; localidades: mapea `point`) y deps/rutas son el idiom de FastAPI. Barrios no entraría en el repo genérico porque su `get_all` selecciona columnas calculadas.

## Open questions
- ¿Extraer un repo base genérico para localidades, divisiones y países (~30 líneas menos, cambio de paginación en un solo sitio) o dejar la copia explícita? Sin decidir.
- ¿El select de división al crear una localidad debe ofrecer divisiones inactivas?

## Next steps
- Front: `AdminPage<T>` genérico, endpoints nuevos en `catalogEndpoints.ts`, tabs de localidades/divisiones/países y pasar el filtro de país al GET admin para ver inactivos.
- Los modales de barrios (editar, geometría, desactivar) siguen en mock.
