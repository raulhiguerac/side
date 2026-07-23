---
title: Integración properties → catalog-service
status: draft
last-verified: 2026-07-19
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[catalog-service]]"
  - "[[adr-geo-enrichment-at-write-time]]"
  - "[[properties-service-listing]]"
  - "[[properties-service-bulk-create-worker]]"
  - "[[properties-service-users]]"
sources:
  - ../../../sources/properties-service/2026-05-28-foundational-exploration.md
  - ../../../sources/frontend/2026-06-28-devcontainer-proxy-chrome-fix.md
  - ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md
---

## TL;DR

properties-service consume [[catalog-service]] **síncronamente en write time** para resolver/validar geografía: al crear un listing valida que el barrio pertenezca a la ciudad, y en el bulk resuelve `(lat, lon) → IDs geográficos` **en batch** (desde 2026-07-19). Cliente HTTP con `httpx`, timeout de 2s por defecto (30s override en la llamada bulk), traducción de errores a un error de dominio. Encarna el principio `[[adr-geo-enrichment-at-write-time]]`.

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `CatalogClient` | `integrations/catalog/catalog_client.py` | Cliente HTTP crudo a catalog (httpx). |
| `CatalogAdapter` | `services/shared/adapters/catalog_adapter.py` | Implementa `CatalogGateway`; traduce dict→schema de dominio. |
| `CatalogGateway` | `services/shared/ports/catalog_gateway.py` | Port que ven los UCs. |
| Schemas | `services/shared/schemas/catalog_schemas.py` | `NeighborhoodInfo`, `LocationInfo`, `PointToResolve`, `ResolvedPoint`. |
| Error mapper | `integrations/catalog/error_mapper.py` | Mapea status HTTP de catalog a `CatalogClientError`. |

## Endpoints consumidos

| Método del client | Endpoint de catalog | Quién lo usa |
|---|---|---|
| `get_neighborhood(neighborhood_id)` | `GET /v1/neighborhoods/by-id` | `CreateProperty` / `UpdateProperty` — validar barrio↔ciudad. |
| `get_locations_bulk(points)` | `POST /v1/geo-resolution/by-coordinates/bulk` | `BulkCreatePropertiesUseCase._process_batch` — resolver un batch de `(lat, lon)` en una sola llamada. |

El port expone `get_neighborhood`, `get_location_by_point` (singular, legacy) y `get_locations_bulk` (batch); el adapter traduce los nombres y formas hacia/desde `CatalogClient`.

### `get_location_by_point`/`get_location_info` — roto desde el cambio a bulk (2026-07-19)

El método singular del client (`get_location_info`, `GET /v1/geo-resolution/by-coordinates`) fue **reemplazado**, no extendido, por `get_locations_bulk` — `CatalogClient` ya no tiene `get_location_info`. `CatalogGateway.get_location_by_point`/`CatalogAdapter.get_location_by_point` siguen declarados y llaman a ese método inexistente; el único caller que quedaba (`_enrich_location`, el flujo viejo fila-por-fila con `asyncio.Semaphore(50)` en `BulkCreatePropertiesUseCase`) es código muerto sin reconciliar — ver [[properties-service-bulk-create-worker]] y el open item en [[open-items]]. Romperlo fue deliberado (decisión explícita de la sesión, no un descuido) mientras se reconstruye el worker para usar el batch.

## Comportamiento de red

- **Timeout fijo de 2s** por request (`self.timeout = 2.0`) — excepto `get_locations_bulk`, que usa un override de **30s** en esa llamada puntual (un batch de cientos/miles de puntos tarda más que un lookup individual).
- `httpx.TimeoutException` → `CatalogClientError("Catalog service timed out")`.
- `httpx.RequestError` (no se pudo conectar) → `CatalogClientError("Could not reach catalog service")`.
- JSON inválido en la respuesta → `CatalogClientError("Catalog service returned invalid JSON")`.
- `CATALOG_URL` no seteada → `CatalogClientError` en construcción del cliente.

Aguas arriba, los UCs traducen estos fallos al error de dominio `CatalogServiceUnavailableError` cuando corresponde.

## Gotcha — `LocationInfo.city_id` necesitaba alias (2026-07-19)

`LocationInfo` tenía `city_id: uuid.UUID` sin alias, pero el campo real que devuelve catalog-service en ese JSON es `locality_id` (`LocationByCoordinates.locality_id`, ver [[catalog-service-poi-lifecycle]]). Sin alias, `model_validate` fallaba por campo faltante — afectaba tanto el flujo singular viejo como el nuevo `ResolvedPoint.location`. Nunca se había detectado porque el flujo end-to-end no se había ejercido contra el catalog real todavía.

**Fix**: `city_id: uuid.UUID = Field(alias="locality_id")`. `model_dump()` sigue devolviendo la clave `city_id` (el alias solo afecta cómo se puebla al validar, no cómo se serializa), así que el código downstream (`row_to_item`, que lee `result["city_id"]`) no se vio afectado. Verificado con un test directo de pydantic contra el shape real.

## Gotcha — schemas de respuesta externa y `extra="forbid"`

`NeighborhoodInfo` y `LocationInfo` en `catalog_schemas.py` originalmente extendían `StrictBase` (`extra="forbid"`). Catalog-service devuelve campos adicionales en la respuesta (`search_name`, `latitude`, `longitude`). Pydantic rechazaba esos campos con `ValidationError`, que era capturado por el `except Exception` genérico de `CatalogAdapter.get_neighborhood()` y re-levantado como `CatalogServiceUnavailableError` → **503**.

**Fix (2026-06-28)**: ambos schemas ahora extienden `_ExternalSchema(BaseModel)` con `model_config = ConfigDict(extra="ignore")`.

**Regla derivada**: los schemas que wrappean respuestas de APIs externas o inter-servicio (cualquier cosa que pase por `model_validate` sobre un dict de HTTP) deben usar `extra="ignore"`. Solo los schemas que definen contratos de input propios del dominio deben usar `extra="forbid"` (`StrictBase`).

## Por qué síncrono en write time

El barrio (`neighborhood_id`) es parte de la identidad del listing y feed de features del AVM: persistir una propiedad con geografía inconsistente corrompería tanto el feed-mapa (índices H3) como el training. Validar en el momento de la escritura (en vez de async/eventual) garantiza que **no entra a la DB un listing con barrio↔ciudad inconsistente**. El costo es acoplar la latencia de create al RTT con catalog (acotado por el timeout de 2s). Ver `[[adr-geo-enrichment-at-write-time]]`.

## Claims

- `CatalogClient` usa `httpx` con timeout fijo de 2.0s ([catalog_client.py:15](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L15)).
- `get_neighborhood` llama `GET {base}/v1/neighborhoods/by-id?neighborhood_id=...` ([catalog_client.py:17-21](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L17-L21)).
- `get_locations_bulk` llama `POST {base}/v1/geo-resolution/by-coordinates/bulk` con `json=points` (lista de dicts `{id, lat, lon}`) y timeout de 30s en esa llamada ([catalog_client.py](backend/properties-service/src/app/integrations/catalog/catalog_client.py)). Reemplazó a `get_location_info` (ya no existe en `CatalogClient`).
- `LocationInfo.city_id` usa `Field(alias="locality_id")` porque el JSON de catalog trae `locality_id`, no `city_id` — sin el alias, `model_validate` fallaba por campo faltante ([catalog_schemas.py](backend/properties-service/src/app/services/shared/schemas/catalog_schemas.py)). `model_dump()` sigue emitiendo `city_id`.
- `PointToResolve(id, lat, lon)` y `ResolvedPoint(id, location: Optional[LocationInfo])` son los schemas locales del contrato bulk, mismo patrón `_ExternalSchema` que `LocationInfo`/`NeighborhoodInfo` ([catalog_schemas.py](backend/properties-service/src/app/services/shared/schemas/catalog_schemas.py)).
- El cliente falla en construcción si `CATALOG_URL` no está seteada ([catalog_client.py:12-14](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L12-L14)).
- Timeout y errores de conexión se mapean a `CatalogClientError` con mensajes distintos ([catalog_client.py:32-35](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L32-L35)).
- El port `CatalogGateway` expone `get_neighborhood` y `get_location_by_point` ([catalog_gateway.py:7-9](backend/properties-service/src/app/services/shared/ports/catalog_gateway.py#L7-L9)).
- `NeighborhoodInfo` trae `id`, `locality_id`, `name` con `extra="ignore"` (`_ExternalSchema`) — catalog devuelve campos extra (`search_name`, `latitude`, `longitude`) que se descartan; la validación barrio↔ciudad compara `locality_id` con el `city_id` del request ([catalog_schemas.py](backend/properties-service/src/app/services/shared/schemas/catalog_schemas.py)).
- `CatalogAdapter.get_neighborhood` tiene un `except Exception` genérico que convierte cualquier error inesperado (incluyendo `ValidationError` de Pydantic) en `CatalogServiceUnavailableError` → 503 — por eso los schemas externos deben nunca usar `extra="forbid"` ([catalog_adapter.py](backend/properties-service/src/app/services/shared/adapters/catalog_adapter.py)).
