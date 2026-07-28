---
title: Integración properties → users-service
status: stable
last-verified: 2026-07-27
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[users-service]]"
  - "[[properties-service-catalog]]"
  - "[[properties-service-bulk-create-worker]]"
sources:
  - ../../../sources/properties-service/2026-07-19-bulk-create-worker-streaming-csv.md
  - ../../../sources/properties-service/2026-07-27-bulk-async-import-worker.md
  - ../../../sources/users-service/2026-07-27-resolve-accounts-by-email.md
---

## TL;DR

Cliente HTTP hacia [[users-service]] con el mismo patrón hexagonal que la integración con catalog: `UsersClient` (httpx crudo) → `UsersAdapter` (implementa `UsersGateway`) → schema local `ResolvedAccount`. Resuelve **`email → account_id`** en batch, y su único consumidor es el bulk-create worker, que lo usa para poblar `Property.owner_id` con el dueño real de cada fila del CSV.

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `UsersClient` | `integrations/users/users_client.py` | Cliente HTTP crudo a users-service (httpx). |
| `UsersAdapter` | `services/shared/adapters/users_adapter.py` | Implementa `UsersGateway`; traduce pares posicionales `[id, email]` → `ResolvedAccount`. |
| `UsersGateway` | `services/shared/ports/users_gateway.py` | Port que ven los UCs/workers. |
| Schema | `services/shared/schemas/users_schemas.py` | `ResolvedAccount(account_id, email)`. |
| Excepción + error mapper | `core/exceptions/listing.py` (`UsersServiceUnavailableError`), `integrations/users/error_mapper.py` (`UsersClientError`) | Propios de users, **no reusan** los de catalog — el primer borrador copiaba `CatalogClientError`/`map_response_error` de catalog por error de copy-paste. |

## Endpoint consumido

| Método del client | Endpoint de users | Quién lo usa |
|---|---|---|
| `resolve_by_emails(emails)` | `POST /v1/users/resolve` | `BulkCreatePropertiesWorker._process_users_batch`, vía `enrich_chunk`. |

`UsersGateway.resolve_accounts(*, emails: list[str]) -> list[ResolvedAccount]` es el método del port. `UsersAdapter` llama `client.resolve_by_emails(emails=emails)` y mapea cada `[id, email]` posicional (la respuesta de users-service no es una lista de objetos, es una lista de tuplas serializadas como arrays de 2 elementos) a `ResolvedAccount(account_id=item[0], email=item[1])`.

## Dirección del resolve — resuelto 2026-07-27

Durante julio este cliente estuvo **construido pero desconectado**: el endpoint de users-service resolvía `account_id → email` (commit `eda7114`), y el bulk-create necesitaba exactamente lo contrario — el CSV trae el `email` del dueño y hace falta el `account_id` para `Property.owner_id`.

Se resolvió **dando vuelta la dirección del endpoint existente** en lugar de agregar uno nuevo: `POST /v1/users/resolve` ahora recibe `list[str]` de emails. Fue un cambio de contrato breaking, seguro únicamente porque un grep confirmó que el stub del worker era su único consumidor. El shape de respuesta no cambió: sigue devolviendo `(account_id, email)`.

En el lado properties, `UsersClient.get_user_ids(ids=...)` se renombró a `resolve_by_emails(emails=...)` — mantener el nombre viejo posteando emails habría sido activamente engañoso.

### Semántica de los emails que no matchean

Un email sin cuenta activa **simplemente no vuelve** en la respuesta, en vez de lanzar error. El consumidor depende de esto: el worker no lo encuentra en `email_cache` y la fila se reporta como `"owner not resolved for email: X"` con su línea de CSV, quedando en `bulk_jobs.errors`. Nunca se asigna a un dueño equivocado ni cae de vuelta al admin importador.

> **Gotcha vigente — case sensitivity.** El lookup es case-sensitive de punta a punta: el filtro SQL (`Account.email.in_(emails)`) y el `email_cache` del worker comparan strings crudos. `StrictBase` hace `str_strip_whitespace` pero **no** normaliza a minúsculas. Si el CSV trae `Raul@Mail.com` y la cuenta está guardada como `raul@mail.com`, la fila falla como "owner not resolved" sin ninguna señal de que la causa fue el casing. Sin decidir si normalizar en escritura, en lectura o ambas.

## Cómo lo usa el worker

`enrich_chunk` (`workers/helpers/enrichment/chunk_enricher.py`) recibe la resolución de emails como **callable inyectado** (`resolve_emails`), no importando el gateway directamente — el worker le pasa su propio `_process_users_batch`. Eso mantiene el helper testeable con un fake.

Por cada chunk se pide solo el delta (`chunk_emails - email_cache.keys()`); si el chunk no trae emails nuevos, la llamada HTTP ni se hace. El `email_cache` sobrevive a todos los chunks de la corrida, así que un owner que se repite a lo largo del archivo cuesta un único round-trip. La llamada corre en paralelo con la geo-resolución vía `asyncio.gather`.

## Claims

- `UsersClient.resolve_by_emails(*, emails: list[str])` hace `POST {base}/v1/users/resolve` con `json=emails` y timeout de 30s ([users_client.py](backend/properties-service/src/app/integrations/users/users_client.py)).
- `UsersGateway.resolve_accounts` toma `emails: list[str]` y devuelve `list[ResolvedAccount]` ([users_gateway.py](backend/properties-service/src/app/services/shared/ports/users_gateway.py)).
- `UsersAdapter.resolve_accounts` mapea la respuesta por **posición** (`item[0]`, `item[1]`), no por `model_validate` — la respuesta de `/v1/users/resolve` es JSON de tuplas serializadas como arrays ([users_adapter.py](backend/properties-service/src/app/services/shared/adapters/users_adapter.py)).
- `UsersServiceUnavailableError` y `UsersClientError` son excepciones propias del dominio users, separadas de `CatalogServiceUnavailableError`/`CatalogClientError` ([core/exceptions/listing.py](backend/properties-service/src/app/core/exceptions/listing.py), [integrations/users/exceptions.py](backend/properties-service/src/app/integrations/users/exceptions.py)).
- `get_users_gateway()` está wireado en `api/deps/listing.py` con `@lru_cache(maxsize=1)` y se inyecta en el worker desde `run_bulk_create_properties` ([listing.py](backend/properties-service/src/app/api/deps/listing.py), [admin.py](backend/properties-service/src/app/api/deps/admin.py)).
- `BulkCreatePropertiesWorker._process_users_batch` delega en `self.users.resolve_accounts(emails=list(emails))` ([bulk_create_properties_worker.py](backend/properties-service/src/app/workers/bulk_create_properties_worker.py)).
- Los emails sin cuenta activa no aparecen en la respuesta de `/v1/users/resolve`; la fila correspondiente se convierte en un `BulkRowError` con el mensaje `"owner not resolved for email"` ([orm_objects.py](backend/properties-service/src/app/workers/helpers/mapping/orm_objects.py)).
- El lookup de email es case-sensitive: `Account.email.in_(emails)` en users-service y `email_cache.get(value.email)` en el worker comparan strings sin normalizar ([account_repository.py](backend/users-service/src/app/repositories/account_repository.py), [orm_objects.py](backend/properties-service/src/app/workers/helpers/mapping/orm_objects.py)).
