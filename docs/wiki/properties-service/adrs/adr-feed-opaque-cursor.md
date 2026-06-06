---
title: ADR-0005 — Cursor de paginación opaco (base64url)
status: stable
last-verified: 2026-06-05
owners: [properties-service]
related: [[properties-service-search]], [[adr-feed-ads-organic-injection]]
sources: [../../../sources/properties-service/2026-06-05-feed-cursor-pagination.md]
decision-date: 2026-06-05
decision-status: accepted
---

# ADR-0005 — Cursor de paginación opaco (base64url)

## Contexto

El feed paginaba con tres query params separados (`cursor_created_at`, `cursor_id`, `cursor_position`). El cliente necesitaba conocer la estructura interna del cursor para construir la siguiente request, lo que acoplaba el contrato de API a detalles de implementación. Además, `FeedPage` no existía — el endpoint devolvía `list[PropertyCardSchema]` sin forma de adjuntar el token de siguiente página.

## Decisión

El cursor se serializa como **token opaco**: `FeedCursor(created_at, id, position)` → `json.dumps(model_dump)` → `UTF-8` → `base64url`. El cliente recibe el token en `FeedPage.next_cursor: str | None` y lo reenvía como `?cursor=<token>` sin interpretarlo. La decodificación ocurre en el UC.

```
encode: FeedCursor → json → bytes → base64url → str
decode: str → base64url → bytes → json → FeedCursor.model_validate()
```

## Consecuencias

- El contrato público es un único param `?cursor=` en lugar de tres — más simple para el cliente.
- La estructura interna del cursor puede cambiar sin romper la API (solo re-generando un token nuevo).
- Un token corrupto o manipulado lanza `InvalidCursorError` → HTTP 400 (registrado en `ERROR_CODE_TO_HTTP_STATUS`).
- `FeedPage` reemplaza `list[PropertyCardSchema]` como response del endpoint, habilitando el transporte del `next_cursor`.
- `parse_feed_cursor` (dep de 3 params) fue eliminado; el endpoint recibe `cursor: Optional[str] = Query(default=None)` directamente.

## Alternativas descartadas

- **3 query params separados** — requería que el cliente construyera el cursor a mano; además `PropertyCardSchema` no expone `created_at`, por lo que era imposible desde el front.
- **Cursor firmado (HMAC)** — previene manipulación pero añade complejidad innecesaria; el cursor no da acceso a datos sensibles.

## Claims

- `encode_cursor` serializa `FeedCursor` a base64url y `decode_cursor` invierte el proceso ([encoding.py](backend/properties-service/src/app/services/search/helpers/feed/encoding.py)).
- `decode_cursor` lanza `InvalidCursorError` (HTTP 400) ante cualquier fallo de base64, JSON o validación de schema ([encoding.py:12-18](backend/properties-service/src/app/services/search/helpers/feed/encoding.py#L12-L18)).
- El endpoint devuelve `FeedPage` con `next_cursor: str | None`; `None` indica que no hay más páginas ([search.py:21](backend/properties-service/src/app/api/routes/search.py#L21), [feed_schemas.py:25-27](backend/properties-service/src/app/services/search/schemas/feed_schemas.py#L25-L27)).
