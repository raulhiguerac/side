---
title: Integración Mapbox (catalog-service)
status: draft
last-verified: 2026-07-15
owners: [catalog-service]
related:
  - "[[catalog-service-architecture]]"
  - "[[adr-mapbox-frontend-only]]"
  - "[[glossary]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Mapbox Geocoder API se usa hoy desde el backend para [[glossary#forward-geocoding]] (`address → lat/lon`) dentro del UC legacy `ResolveNeighborhoodUseCase`. **Esta integración está marcada para eliminación** post-refactor de `/geo-resolution` (ver [[adr-mapbox-frontend-only]]) — el frontend ya hace este hop con Mapbox SDK. Documentado aquí mientras el código exista.

## Configuración

Una sola env var:

| Env | Para qué | Default |
|---|---|---|
| `MAPBOX_API_KEY` | Token de la API de Mapbox Geocoder | — (sin default, falla en runtime si no está) |

Lectura: directo de `os.getenv()` en `GeoreferentiationClient.__init__` ([mapbox/georeferentiation.py:21](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L21)). **No** está modelada en `Settings`.

Si falta, la primera request a `forward_geocode` lanza `GeoResolutionMisconfiguredError(context={"missing": "MAPBOX_API_KEY"})`.

## API surface

### Cliente bajo nivel: `GeoreferentiationClient` ([integrations/georef/mapbox/georeferentiation.py](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py))

Wrappea el SDK `mapbox` (pip `mapbox>=0.18.1`). Un solo método público:

```python
async def forward_geocoding(
    *,
    address: str,
    country_code: str,
    proximity: tuple[float, float] | None = None,
) -> dict:
```

- Construye un `mapbox.Geocoder(access_token=...)` por llamada (no cachea el cliente).
- Filtra por `country` (lowercase del `country_code` ISO alpha-2).
- Si `proximity` viene, lo pasa para sesgar resultados a una zona (lat/lon de la locality).
- Ejecuta `geocoder.forward(address, **kwargs)` envuelto en `asyncio.to_thread` (SDK es sync).
- Devuelve el GeoJSON raw response.

### Port + adapter: `GeocodingGateway` + `GeocodingAdapter`

El UC (`ResolveNeighborhoodUseCase`) no toca el cliente bajo nivel — depende del port [`GeocodingGateway`](backend/catalog-service/src/app/services/geo_resolution/ports/geocoding/gateway.py) (movido de `ports/geocoding_gateway.py` a `ports/geocoding/gateway.py` en la reorganización de `geo_resolution`).

[`GeocodingAdapter`](backend/catalog-service/src/app/services/geo_resolution/adapters/geocoding/mapbox.py) implementa el port (movido de `adapters/geocoding.py` a `adapters/geocoding/mapbox.py`):

1. Llama `GeoreferentiationClient.forward_geocoding(...)`.
2. Extrae el primer feature del response.
3. Construye un `GeocodingResult(latitude, longitude, formatted_address)`.
4. Si no hay features o falta `geometry.coordinates` → `GeoResolutionNotFoundError`.

Esta capa de adapter aísla el dominio de la forma del GeoJSON de Mapbox.

## Error mapping

El cliente captura excepciones de la librería + `requests` y las traduce a errores de dominio. Cuatro categorías:

| Excepción interna | Error de dominio | HTTP equivalente |
|---|---|---|
| `mapbox.errors.ValidationError` | `GeoResolutionBadRequestError` | 400 |
| `requests.exceptions.ConnectionError`, `Timeout` | `GeoResolutionUnavailableError` | 503 |
| `requests.exceptions.HTTPError` (cualquier status) | `GeoResolutionUnavailableError` | 503 |
| (faltante) `MAPBOX_API_KEY` | `GeoResolutionMisconfiguredError` | 503 |
| Response sin `features` | `GeoResolutionNotFoundError` | 404 |

Todos extienden `BaseError` de `core/exceptions/base.py` (mismo handler global).

## Caching del resultado

El cache vive **en el UC, no en el adapter** — el UC `ResolveNeighborhoodUseCase` chequea `cache_key_forward_geocode(query, locality_id)` en Redis **antes** de llamar al adapter, y guarda el `(lat, lon)` resultado con TTL `CACHE_TTL_ENTITY_SECONDS` (30 días). Detalle en [[catalog-service-architecture]] sección "Caching strategies".

Beneficio: el segundo lookup de la misma dirección dentro de la misma locality no toca Mapbox.

## Deprecación pendiente

Toda esta integración debería desaparecer del backend según [[adr-mapbox-frontend-only]]:

- Eliminar `integrations/georef/mapbox/` completo.
- Eliminar `GeocodingGateway`, `GeocodingAdapter`, `GeocodingResult`.
- Eliminar `ResolveNeighborhoodUseCase`.
- Quitar `MAPBOX_API_KEY` del entorno del backend.
- Quitar `mapbox>=0.18.1` de `pyproject.toml`.
- Frontend mantiene Mapbox SDK para autocomplete + preview (sin cambios).

Hasta entonces, esta página describe lo que hay.

## Claims

- `GeoreferentiationClient` se construye instanciando `mapbox.Geocoder` con el token leído de `MAPBOX_API_KEY` directamente del entorno ([mapbox/georeferentiation.py:21-26](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L21-L26)).
- La llamada SDK va envuelta en `asyncio.to_thread` porque el SDK de Mapbox es síncrono ([mapbox/georeferentiation.py:32](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L32)).
- 4 categorías de error mapeadas: `ValidationError` → BadRequest, `ConnectionError`/`Timeout` → Unavailable, `HTTPError` → Unavailable, missing token → Misconfigured ([mapbox/georeferentiation.py:34-56](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L34-L56)).
- `MAPBOX_API_KEY` no está en el `Settings` modelo — se lee directo de `os.getenv` ([mapbox/georeferentiation.py:21](backend/catalog-service/src/app/integrations/georef/mapbox/georeferentiation.py#L21)).
- El cache de forward geocode (30 días) vive en el UC, no en el adapter ni en el cliente ([resolve_neighborhood.py:56-87](backend/catalog-service/src/app/services/geo_resolution/use_cases/resolve_neighborhood.py#L56-L87)).
- Esta integración está marcada como **deprecada** post-refactor de `/geo-resolution` (ver [[adr-mapbox-frontend-only]]).
- El port/adapter de geocoding se movieron a subcarpetas propias en la reorganización de `geo_resolution`: `ports/geocoding/gateway.py` y `adapters/geocoding/mapbox.py` (antes `ports/geocoding_gateway.py` y `adapters/geocoding.py`).
- La ausencia de `MAPBOX_API_KEY` mapea a HTTP **503** (no 500) vía `GeoResolutionMisconfiguredError` ([exception_handlers.py:15](backend/catalog-service/src/app/api/handlers/exception_handlers.py#L15)).
