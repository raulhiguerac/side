---
title: ADR-0003 — Action tokens de un solo uso en Redis
status: stable
last-verified: 2026-05-28
owners: [users-service]
related:
  - "[[users-service-auth]]"
  - "[[users-service-user]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
decision-date: 2026-05-28
decision-status: accepted
---

# ADR-0003 — Action tokens de un solo uso en Redis

## Contexto

Dos flujos por email necesitan un token que el usuario presenta para autorizar una acción sensible sin sesión: **reset de contraseña** y **reactivación de cuenta**. El token viaja en una URL enviada por email y se redime en un segundo request. Hay que decidir cómo generarlo, dónde guardarlo, y cómo garantizar un solo uso.

## Decisión

- **Token opaco aleatorio**: `secrets.token_urlsafe(32)` — no es un JWT, no codifica claims.
- **Almacenamiento en Redis** con la clave = `hash_token(token)` (se guarda el hash, no el token crudo) y el valor = `{account_id}`, con TTL.
- **Un solo uso vía `GETDEL`**: el confirm consume el token de forma atómica (lee y borra en una operación). Un segundo intento con el mismo token no encuentra nada → inválido.
- **Transporte por Bearer header** en el confirm (no cookie) — es una acción puntual, no una sesión.
- **Respuestas que no filtran existencia**: el request siempre responde 202 genérico; si la cuenta no existe o está inactiva, se retorna en silencio.

## Alternativas consideradas

- **JWT firmado con expiración** — sin estado servidor, pero **no es revocable ni de un solo uso** sin una lista de denegación; un token robado vale hasta que expira. El opaco + GETDEL da un solo uso real.
- **Token en la DB** (tabla de tokens) — funciona y es durable, pero agrega una tabla + limpieza de expirados; Redis con TTL expira solo y es ideal para datos efímeros.
- **Guardar el token en crudo en Redis** — si Redis se compromete, los tokens activos son usables. Guardar el hash limita el daño.

## Consecuencias

- ✅ Un solo uso real y atómico (`GETDEL`) — no hay ventana de replay.
- ✅ Expiración automática por TTL — sin job de limpieza.
- ✅ Guardar el hash protege ante una lectura no autorizada de Redis.
- ✅ No filtra qué emails están registrados.
- ❌ **Depende de Redis**: si Redis está caído, los flujos de reset/reactivación no funcionan (y un flush de Redis invalida todos los tokens en vuelo).
- ❌ El token vive solo en Redis — no hay rastro de auditoría persistente de los resets emitidos/consumidos (solo logs).
- ❌ Mismo mecanismo para dos flujos distintos comparte el riesgo: un bug en `hash_token`/keys afecta a ambos.

## Claims

- El token es `secrets.token_urlsafe(32)`, guardado en Redis bajo `hash_token(token)` con el `account_id` como valor ([request_reset_password.py:34-41](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L34-L41)).
- El confirm consume el token con `getdel_json` (atómico, un solo uso) ([confirm_reset_password.py:59-67](backend/users-service/src/app/services/auth/use_cases/confirm_reset_password.py#L59-L67)).
- El token del confirm llega vía Bearer header (`HTTPBearer`) ([action_token.py:4-9](backend/users-service/src/app/api/deps/action_token.py#L4-L9)).
- El request retorna en silencio si la cuenta no existe o está inactiva ([request_reset_password.py:31-32](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L31-L32)).
- El mismo patrón se usa para reactivación de cuenta ([users-service-user](docs/wiki/users-service/domain/users-service-user.md)).
