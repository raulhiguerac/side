---
title: Fix Overpass 406/ServerLoadError y huevo-gallina de h3_cells en by-coordinates
captured-from: conversation
captured-on: 2026-06-23
participants: [raul, claude]
---

## Context

`GET /v1/geo-resolution/by-coordinates` empezó a devolver 404 "no neighborhood found" para coordenadas válidas de Bogotá, y por separado el populate-on-demand de POIs (`ResolvePoiUseCase`) fallaba silenciosamente contra Overpass. Se investigaron ambos en la misma sesión porque están en la misma cadena (`by-coordinates` → `ResolvePoiUseCase` → `PoiClient`).

## Key conclusions

- **Causa del 404**: el commit que agregó `BackgroundTasks` a `/by-coordinates` también agregó un prefiltro `.where(Neighborhood.h3_cells.any(cell))` en `get_location_by_point` — pero `h3_cells` solo se puebla como side-effect de una resolución previa. Para una celda nunca vista, el prefiltro descartaba todo antes de llegar a `ST_Contains`, y como el use case lanzaba la excepción antes de programar el `background_tasks.add_task`, la celda nunca se poblaba (huevo-gallina).
- **Fix aplicado**: `get_location_by_point` ahora hace `h3_cells.any(cell)` + `ST_Contains` juntos (acota candidatos a 1-3 barrios vecinos cuando la celda ya está poblada, pero `ST_Contains` sigue siendo el que decide cuál es el barrio correcto — evita el edge case de bordes donde una celda H3 solapa 2 barrios). Si no hay candidatos por `h3_cells` (celda fría), cae a un `ST_Contains` completo sobre todos los barrios con `geom`. El `background_tasks.add_task(poi_uc.execute, ...)` en `/by-coordinates` se restauró.
- **Bug de logging descubierto en el camino**: `setup_logging()` (`core/logging/logger.py`) usa un formato fijo con solo `%(message)s` — cualquier `extra={...}` pasado a `logger.error/warning` se descarta siempre, en todo el servicio. Por eso el log de Overpass nunca mostraba la razón real del error. Se corrigió interpolando el motivo directo en el mensaje (`overpass.py`, `resolve_poi.py`).
- **Causa real del error de Overpass, una vez visible**: `overpass-api.de` devuelve **406** a requests con el `User-Agent` genérico de `python-requests`/`curl` — confirmado con curl directo (sin UA custom → 406; con UA descriptivo → 200). No es un bug de la librería `overpass` ni de nuestra query QL; es una política del servidor público, probablemente antibots, que empezó a aplicarse en algún momento sin que cambiáramos nada de nuestro lado.
- **Fix**: `PoiClient` ahora pasa `headers={"User-Agent": settings.OVERPASS_USER_AGENT, "Accept-Charset": ...}` a `overpass.API(...)`. Nuevo setting `OVERPASS_USER_AGENT` con default razonable.
- **Excepciones de la librería `overpass` no son subclases de `requests.exceptions`** — `OverpassSyntaxError` (400), `MultipleRequestsError` (429), `ServerLoadError` (504), `UnknownOverpassError` (otros códigos) caían todas en el `except Exception` genérico. Se agregaron excepts específicos para loggear la causa exacta sin perder la traza.
- Tras el fix de User-Agent, apareció un `ServerLoadError` (504) bajo carga — es la instancia pública sobrecargada, no algo corregible desde el código. Se documentó como ítem de backlog para evaluar self-host de Overpass (requiere subir/mantener `.pbf` de Colombia/Bogotá).
- Bug no relacionado encontrado en el camino: `BulkCreateNeighborhoodsUseCase.bulk_insert` (vía `n.model_dump()`) serializaba `created_at`/`updated_at` como `NULL` explícito (son `server_default`, sin default de Python), violando el `NOT NULL` y forzando que el bulk insert **siempre** cayera al fallback fila-por-fila. Fix: `model_dump(exclude={"created_at", "updated_at"})`.

## Open questions

- ¿Vale la pena el self-host de Overpass dado el costo operativo de mantener `.pbf` actualizados? Queda en `docs/wiki/_shared/open-items.md` sin decisión tomada.

## Next steps

- Monitorear si el `ServerLoadError` se repite seguido; si sí, priorizar la evaluación de self-host o un mirror alternativo (`overpass.kumi.systems`) con retry/backoff.
