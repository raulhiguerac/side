---
title: Read path admin de barrios y catalog admin organizado por entidad
captured-from: conversation
captured-on: 2026-10-04
participants: [author, claude]
---

## Context
catalog-service no tenía ningún `GET` admin: la tab de barrios del panel no podía listar, ver el detalle ni pintar vecinos, y la geometría solo se escribía. Se construyó el read path de barrios y, de paso, se reorganizó catalog admin porque `routes/admin.py` y `deps/catalog_admin.py` crecían sin control.

## Key conclusions
- Casos de uso, rutas y deps de catalog admin van en una carpeta por entidad (`country`, `admin_division`, `locality`, `neighborhood`), igual que ports, adapters y schemas. Los tests replican la estructura.
- `routes/admin/__init__.py` monta `prefix="/admin"`, tags y `require_admin`; los subrouters van sin prefix porque los bulk de barrios viven bajo `/localities/{id}/neighborhoods/...`. En `deps/catalog_admin/`, `get_uow` está en `uow.py` y el `__init__` queda vacío.
- Las lecturas admin no usan cache: el admin escribe y mira la misma pantalla para comprobar el resultado.
- `GET /v1/admin/neighborhoods`: paginado por offset. Request `page`, `page_size` (≤100), `locality_id`, `is_active`, `has_geometry`, `search_term`. Respuesta `items`, `total_items`, `total_pages`, `current_page`, `items_per_page`, `coverage`. Se eligieron nombres descriptivos aunque difieren de `total/page/page_size` de properties.
- `search_term` se normaliza igual que `search_name` y filtra con `LIKE` + `autoescape`. Sin índice: ~1,2k filas y el front aplica debounce; si crece, `pg_trgm`.
- Cada item lo arma el adapter con columnas calculadas en PostGIS (`has_geometry`, `svg_path` con `ST_AsSVG(rel=1, 5 decimales)`, `bbox` como array) y `model_validate(row)`. Se seleccionan columnas sueltas para no cargar `geom` ni `h3_cells`.
- `get_all`, `count_all` y `get_coverage` comparten `_apply_filters`. `coverage` (con geometría / total) ignora `has_geometry`; si no, la barra marcaría siempre 0 % o 100 %.
- Descartado calcular coverage en el front por página (engañoso) y cachear conteos por checksum del request (~1 ms en Postgres, invalidación en cinco casos de uso de escritura, dato desfasado justo después de escribir).
- Tolerancia de simplificación `0.00001°` (~1,1 m) para listado y detalle: GeoJSON promedio 9,2 → 1,7 KB (máx. 247 → 46 KB), SVG promedio 4,6 → 1,3 KB, el área cambia ≤1,1 %. Con ~5,5 m el área cambia hasta 25 %.
- `GET /v1/admin/neighborhoods/{id}` devuelve `NeighborhoodAdminDetail` (hereda de `NeighborhoodAdminResponse` + `geometry` GeoJSON + `area_m2`). El área se calcula sobre la geometría original como `geography`; sobre `geometry` 4326 saldría en grados². Si no existe → 404 `NEIGHBORHOOD_ADMIN_NOT_FOUND`.
- `get_by_id` del repo se mantiene para las escrituras (necesitan el modelo ORM); el detalle usa un `get_detail` aparte.
- Al simplificar, 1196 de 1202 `MULTIPOLYGON` de una sola parte vuelven como `Polygon`; el front tiene que aceptar ambos tipos.
- Vértices (`ST_NPoints`) fuera hasta que exista un aviso de calidad de geometría.
- `GET /v1/admin/neighborhoods/geometries`: el front manda el bbox visible (`map.getBounds()`) y el `neighborhood_id` a excluir. Usa `ST_Intersects` (con `ST_Contains` se perderían los vecinos que salen del bbox), recorta con `ST_ClipByBox2D` y simplifica. Usa el índice GiST `ix_neighborhood_geom`. Devuelve una lista `{id, name, geometry}`, no un FeatureCollection; el front la convierte a Features.
- La ruta `/neighborhoods/geometries` va antes que `/neighborhoods/{id}`; si no, FastAPI toma "geometries" como id.
- El bbox se valida en el schema: rangos con `ge`/`le`, `min < max` y lado máximo `0.135°` (~15 km) en un `model_validator`. En la ruta va como `Annotated[Req, Query()]`: con `Depends()`, FastAPI trata la `tuple` como body. El bbox llega repetido (`?bbox=…&bbox=…`).
- El hook `pre-commit` (wiki staleness) solo funciona dentro del devcontainer; en el host falla con "pre-commit not found".

## Open questions
- `total_pages` sale 0 cuando no hay resultados: ¿dejarlo o forzar 1?
- Sin `locality_id`, `coverage` mide todo el catálogo filtrado; ¿mandarlo siempre o solo con localidad?
- ¿bbox con comas (`?bbox=a,b,c,d`) en lugar de repetido?
- Barrios con nombre repetido en la base ("El Bagazal", "El Refugio"): ¿homónimos o duplicados de origen?

## Next steps
- `GET` admin de localidades, divisiones (no existe ni público) y países, incluyendo inactivos: los públicos filtran `is_active == True`.
- Tests de integración del adapter con PostGIS (`_apply_filters`, coverage, `get_geometries`).
- Arreglar 7 tests rojos preexistentes: 5 por cambio de firma de `GetNeighborhoodsByLocalityUseCase.execute`, 2 porque el caso de uso no tolera Redis caído.
- Extraer la normalización de `search_name`, copiada en 7 lugares, a un helper compartido.
- Limpieza de comentarios sobreexplicados (tests de users-service, `models/location.py`, banners en `src`).
- Mover los commits a una rama propia desde `main` y hacer push.
