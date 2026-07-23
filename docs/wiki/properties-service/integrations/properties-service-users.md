---
title: Integración properties → users-service
status: draft
last-verified: 2026-07-19
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[users-service]]"
  - "[[properties-service-catalog]]"
  - "[[properties-service-bulk-create-worker]]"
sources:
  - ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md
---

## TL;DR

Cliente HTTP nuevo (2026-07-19) hacia [[users-service]], mismo patrón hexagonal que la integración con catalog: `UsersClient` (httpx crudo) → `UsersAdapter` (implementa `UsersGateway`) → schema local `ResolvedAccount`. Hoy resuelve `account_id → email` en batch; el bulk-create de properties necesita la dirección contraria (`email → account_id`), así que todavía no está conectado al flujo real — ver Gotcha abajo.

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `UsersClient` | `integrations/users/users_client.py` | Cliente HTTP crudo a users-service (httpx). |
| `UsersAdapter` | `services/shared/adapters/users_adapter.py` | Implementa `UsersGateway`; traduce pares posicionales `[id, email]` → `ResolvedAccount`. |
| `UsersGateway` | `services/shared/ports/users_gateway.py` | Port que ven los UCs. |
| Schema | `services/shared/schemas/users_schemas.py` | `ResolvedAccount(account_id, email)`. |
| Excepción + error mapper | `core/exceptions/listing.py` (`UsersServiceUnavailableError`), `integrations/users/error_mapper.py` (`UsersClientError`) | Propios de users, **no reusan** los de catalog — el primer borrador copiaba `CatalogClientError`/`map_response_error` de catalog por error de copy-paste. |

## Endpoint consumido

| Método del client | Endpoint de users | Quién lo usa |
|---|---|---|
| `get_user_ids(ids)` | `POST /v1/users/resolve` | Ninguno todavía en el flujo real — ver Gotcha. |

`UsersGateway.resolve_accounts(*, account_ids: list[uuid.UUID]) -> list[ResolvedAccount]` es el método del port; `UsersAdapter` llama `client.get_user_ids(ids=account_ids)` y mapea cada `[id, email]` posicional (la respuesta de users-service no es una lista de objetos, es una lista de tuplas serializadas como arrays de 2 elementos) a `ResolvedAccount(account_id=item[0], email=item[1])`.

## Bugs corregidos en el draft inicial de `UsersClient`

1. **`uuid.UUID` no es serializable por `json=` de httpx** — el `POST` fallaba con `TypeError`. Fix: `json=[str(i) for i in ids]`.
2. **`list[tuple(uuid.UUID, str)]`** — `tuple(...)` llama al constructor en vez de usar `tuple[...]` como subscript genérico. Fix: `list[tuple[uuid.UUID, str]]`.
3. **URL incorrecta** (`/v1/accounts/resolve` en el draft) — el endpoint real, verificado contra el mount de users-service (`main.py` prefix `/v1` + router `user.py` prefix `/users`), es `/v1/users/resolve`.
4. **Reusaba `CatalogClientError`/`map_response_error` de `integrations/catalog/`** — corregido con excepción y mapper propios (ver tabla de Componentes).

## Gotcha — dirección del resolve, no conectado al bulk-create todavía

`AccountReaderPort.get_accounts_bulk` (users-service, commit `eda7114`) toma `account_ids: list[uuid.UUID]` y devuelve `(account_id, email)` — resuelve **ID → email**. El bulk-create de properties necesita lo opuesto: el CSV trae `email` del dueño real, y necesita el `account_id` para poblar `Property.owner_id` (ver [[properties-service-bulk-create-worker]] y el open item de resolución de owner por email). Con el endpoint actual **no se puede resolver eso** — falta un endpoint de users-service que filtre por `email` y devuelva `account_id`, o cambiar la firma del existente. No implementado — bloqueante para conectar `UsersGateway` al flujo real del bulk-create.

## Claims

- `UsersClient.get_user_ids(*, ids: list[uuid.UUID])` hace `POST {base}/v1/users/resolve` con `json=[str(i) for i in ids]` y timeout de 30s ([users_client.py](backend/properties-service/src/app/integrations/users/users_client.py)).
- `UsersServiceUnavailableError` y `UsersClientError` son excepciones propias del dominio users, separadas de `CatalogServiceUnavailableError`/`CatalogClientError` ([core/exceptions/listing.py](backend/properties-service/src/app/core/exceptions/listing.py), [integrations/users/exceptions.py](backend/properties-service/src/app/integrations/users/exceptions.py)).
- `UsersAdapter.resolve_accounts` mapea la respuesta por **posición** (`item[0]`, `item[1]`), no por `model_validate` de un objeto — la respuesta de `/v1/users/resolve` es JSON de tuplas serializadas como arrays, no objetos con keys ([users_adapter.py](backend/properties-service/src/app/services/shared/adapters/users_adapter.py)).
- `get_users_gateway()` está wireado en `api/deps/listing.py` junto a `get_catalog_gateway()`, mismo patrón `@lru_cache(maxsize=1)` — pero **no** está inyectado todavía en `get_bulk_create_properties_uc` (`api/deps/admin.py`) ([listing.py](backend/properties-service/src/app/api/deps/listing.py)).
- El endpoint de users-service resuelve `account_id → email`, no `email → account_id` — dirección incompatible con el caso de uso de resolución de `owner_id` del bulk-create ([users-service AccountReaderPort](backend/users-service/src/app/services/shared/ports/account_reader.py)).
