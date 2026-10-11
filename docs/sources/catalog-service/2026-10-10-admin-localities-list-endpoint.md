---
title: GET admin de localidades y plan para los tabs de países, divisiones y localidades
captured-from: conversation
captured-on: 2026-10-10
participants: [raul, claude]
---

## Context
El front admin de catálogo tiene conectados los 8 endpoints de barrios; los POST/PATCH de países, divisiones y localidades no se pueden conectar porque no hay GET admin que liste esas entidades incluyendo inactivas. Se empezó por localidades (rama `feat/catalog-admin-list-localities`).

## Key conclusions
- Los GET públicos de `geo_catalog` filtran `is_active == True` fijo en el adapter (`get_active_*` de countries, localities, neighborhoods) y van cacheados; es correcto para el público y **no se parametrizan**: el admin tiene sus propios GET en `catalog_admin`, como barrios.
- `GET /v1/admin/localities` (`ListLocalitiesUseCase`) recibe `GetAllLocalitiesRequest` como `Depends()`: `country_id`, `admin_division_id`, `is_active` opcionales + `page_size` (1–100, def. 20) y `offset` (≥0).
- Responde `GetAllLocalitiesPage { items, total_items }`; cada item es `GetAllLocalitiesResponse` con `id, code, name, locality_type, point {latitude, longitude}, is_active, is_capital`. El `point` anidado queda listo para un mapa futuro.
- `Locality` guarda lat/lng como columnas planas, así que `model_validate` no arma `point`: el use case mapea a mano con una list comprehension (más explícito que un `model_validator(mode="before")` en el schema).
- Repo: `_apply_filters` compartido por `get_all` (con `order_by(name, id)`, `offset`, `limit`) y `count_all` (`select(func.count()).select_from(Locality)`), igual que barrios; `is_active` se compara con `is not None` para que el filtro `false` funcione.
- El `try/except → translate_db_error` envuelve solo las llamadas al repo; el mapeo queda fuera para que un bug de mapeo no se reporte como error de DB.
- Paginación por `offset` (barrios usa `page`): el front calcula `total_pages = ceil(total_items / page_size)` y la página actual.
- Para el front de los tres tabs se prefiere un marco compartido (tabla, modal de estado genérico, `EntityFormModal` con slot) + un componente de campos por entidad, en vez de un form 100 % por config: la cascada país → división y los campos inmutables en edición lo harían un mini motor de formularios.
- La geo-resolución (`/resolve-neighborhood`, `/by-coordinates`) no filtra por `is_active`: un barrio desactivado se sigue resolviendo. No está documentado si es intencional.

## Open questions
- ¿Se cambia `offset` por `page` para reusar tal cual el paginador de barrios?
- `GetLocalityByIdRequest` hereda la paginación del base; si se usa, separar filtros de paginación.
- ¿Se agrega `extend-immutable-calls = ["fastapi.Depends", "fastapi.Query"]` en ruff del servicio? Hoy `B008` salta en todas las rutas y deps y el hook post-edit las bloquea.
- ¿La geo-resolución debe ignorar barrios inactivos?

## Next steps
- Back: GET admin de divisiones por país (desbloquea crear localidad y el filtro de división; hoy no existe ningún GET de divisiones).
- Back: sumar `local_name` y `timezone` a la respuesta (o un detalle por id) para prellenar el modal de editar.
- Back: GET admin de países con los campos que hoy faltan en `CountryResponse` (`official_name`, `native_name`, `default_locale`, `iso_numeric`).
- Front: tras mergear `feat/front-admin-neighborhoods-crud` (trae el `operationId` corto) y este back, `make generate-types` y armar el tab de localidades desde `main`.
