---
title: Cache-aside para reachable-pois (isócronas) — diseño y bug de DI
captured-from: conversation
captured-on: 2026-06-20
participants: [raul, claude]
---

## Context

`ResolveIsochroneUseCase` (catalog-service) llamaba a ORS sin caché en cada request. Se diseñó e implementó cache-aside para `reachable-pois`, y en el camino se encontró un bug de inyección de dependencias que dejaba la ruta rota en producción silenciosa (requests "stalled" sin respuesta).

## Key conclusions

- Cache key: si la request trae `property_id`, key estática `geo:reachable:property:{id}`; si no (caso AVM, lat/lon variable), se snappea a la celda H3 r9 del punto (`h3.latlng_to_cell`) y se usa `geo:reachable:cell:{h3_cell}` — mismo grano que ya usa el sistema para bucketear POIs, así que el desfase visual es aceptable (se nota solo en walking con rangos cortos, irrelevante en bici/auto).
- Es todo-o-nada por request: ORS siempre devuelve los 3 profiles fijos en una sola llamada (`asyncio.gather`), así que no existe cache parcial por perfil.
- El check de cache va **antes** de llamar a `gateway.get_isochrones` (fail-fast en hit, evita el costo de ORS).
- Solo se cachea la response si ningún profile dio error; TTL nuevo `settings.CACHE_TTL_ISOCHRONE_SECONDS` (1h, antes hardcodeado a `3600`).
- `try/except Exception: pass` alrededor de llamadas a cache es **redundante en catalog-service**: `CacheClient.get_json`/`set_json` ya atrapan la excepción de Redis internamente y devuelven `None`/`False` — se quitó ese wrapper de `ResolveNeighborhoodUseCase` y `ResolvePoiUseCase`. Pendiente verificar si las copias de `CacheClient` en properties-service/users-service hacen lo mismo (ya divergieron entre sí).
- **Bug real encontrado**: `resolve_isochrone_uc` (DI provider) nunca inyectaba `cache` al construir `ResolveIsochroneUseCase` — faltaba el argumento requerido. Esto causaba que las requests a `/reachable-pois` quedaran "stalled" indefinidamente en el browser en vez de devolver un error limpio. Fix: agregar `cache: CachePort = Depends(get_cache_port)` al provider.

## Open questions

- Invalidación cruzada: cuando se actualiza/borra una propiedad en properties-service, nadie invalida `geo:reachable:property:{property_id}` en catalog-service. Es viable sin llamada cross-service porque Redis es una instancia única compartida entre los tres MS — pero properties-service tendría que conocer el formato de una key que no le pertenece. Se anotó como extensión del ítem de la lib compartida de infra (`adr-shared-infra-lib`).
- Falta confirmar si los `CacheClient` de properties-service/users-service también atrapan excepciones de Redis internamente (para saber si el wrapper redundante aplica ahí también).

## Next steps

- Extender el paquete compartido de infra (cuando se haga) para incluir también los builders de cache key, no solo el cliente Redis — resolvería gratis el problema de invalidación cruzada.
- Validar el punto de la redundancia del `try/except` en properties-service y users-service.
