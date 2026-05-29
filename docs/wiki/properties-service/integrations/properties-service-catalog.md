---
title: Integración properties → catalog-service
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related: [[properties-service]], [[catalog-service]], [[adr-geo-enrichment-at-write-time]], [[properties-service-listing]]
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

properties-service consume [[catalog-service]] **síncronamente en write time** para resolver/validar geografía: al crear un listing valida que el barrio pertenezca a la ciudad, y en el bulk resuelve `(lat, lon) → IDs geográficos`. Cliente HTTP con `httpx`, timeout de 2s, traducción de errores a un error de dominio. Encarna el principio `[[adr-geo-enrichment-at-write-time]]`.

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `CatalogClient` | `integrations/catalog/catalog_client.py` | Cliente HTTP crudo a catalog (httpx). |
| `CatalogAdapter` | `services/shared/adapters/catalog_adapter.py` | Implementa `CatalogGateway`; traduce dict→schema de dominio. |
| `CatalogGateway` | `services/shared/ports/catalog_gateway.py` | Port que ven los UCs. |
| Schemas | `services/shared/schemas/catalog_schemas.py` | `NeighborhoodInfo`, `LocationInfo`. |
| Error mapper | `integrations/catalog/error_mapper.py` | Mapea status HTTP de catalog a `CatalogClientError`. |

## Endpoints consumidos

| Método del client | Endpoint de catalog | Quién lo usa |
|---|---|---|
| `get_neighborhood(neighborhood_id)` | `GET /v1/neighborhoods/by-id` | `CreateProperty` / `UpdateProperty` — validar barrio↔ciudad. |
| `get_location_info(lat, lon)` | `GET /v1/geo-resolution/by-coordinates` | `BulkCreateProperties` — resolver lat/lon → IDs. |

El port expone `get_neighborhood` y `get_location_by_point`; el adapter traduce los nombres y formas hacia/desde `CatalogClient`.

## Comportamiento de red

- **Timeout fijo de 2s** por request (`self.timeout = 2.0`).
- `httpx.TimeoutException` → `CatalogClientError("Catalog service timed out")`.
- `httpx.RequestError` (no se pudo conectar) → `CatalogClientError("Could not reach catalog service")`.
- JSON inválido en la respuesta → `CatalogClientError("Catalog service returned invalid JSON")`.
- `CATALOG_URL` no seteada → `CatalogClientError` en construcción del cliente.

Aguas arriba, los UCs traducen estos fallos al error de dominio `CatalogServiceUnavailableError` cuando corresponde.

## Por qué síncrono en write time

El barrio (`neighborhood_id`) es parte de la identidad del listing y feed de features del AVM: persistir una propiedad con geografía inconsistente corrompería tanto el feed-mapa (índices H3) como el training. Validar en el momento de la escritura (en vez de async/eventual) garantiza que **no entra a la DB un listing con barrio↔ciudad inconsistente**. El costo es acoplar la latencia de create al RTT con catalog (acotado por el timeout de 2s). Ver `[[adr-geo-enrichment-at-write-time]]`.

## Claims

- `CatalogClient` usa `httpx` con timeout fijo de 2.0s ([catalog_client.py:15](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L15)).
- `get_neighborhood` llama `GET {base}/v1/neighborhoods/by-id?neighborhood_id=...` ([catalog_client.py:17-21](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L17-L21)).
- `get_location_info` llama `GET {base}/v1/geo-resolution/by-coordinates?lat&lon` ([catalog_client.py:37-41](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L37-L41)).
- El cliente falla en construcción si `CATALOG_URL` no está seteada ([catalog_client.py:12-14](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L12-L14)).
- Timeout y errores de conexión se mapean a `CatalogClientError` con mensajes distintos ([catalog_client.py:32-35](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L32-L35)).
- El port `CatalogGateway` expone `get_neighborhood` y `get_location_by_point` ([catalog_gateway.py:7-9](backend/properties-service/src/app/services/shared/ports/catalog_gateway.py#L7-L9)).
- `NeighborhoodInfo` trae `id`, `locality_id`, `name`; la validación barrio↔ciudad compara `locality_id` con el `city_id` del request ([catalog_schemas.py:6-9](backend/properties-service/src/app/services/shared/schemas/catalog_schemas.py#L6-L9)).
