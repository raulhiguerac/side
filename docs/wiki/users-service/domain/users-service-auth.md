---
title: Dominio auth — users-service
status: draft
last-verified: 2026-07-15
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-architecture]]"
  - "[[users-service-keycloak]]"
  - "[[adr-keycloak-saga-compensation]]"
  - "[[adr-action-tokens-redis]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

El dominio de **credenciales y sesión**: registro (saga con Keycloak), login/refresh/logout (cookies), cambio de contraseña, y reset de contraseña (token de un solo uso por email). Keycloak es la fuente de verdad de credenciales; la tabla `accounts` es el espejo local.

## Use cases

| UC | Archivo | Qué hace |
|---|---|---|
| `RegisterAccountUseCase` | `use_cases/register_account.py` | Crea usuario en Keycloak + `Account` + perfil; compensa si falla. |
| `AuthenticateAccountUseCase` | `use_cases/authenticate_account.py` | `login` y `refresh_token` contra Keycloak; devuelve tokens. |
| `LogoutUseCase` | `use_cases/logout.py` | Revoca el refresh token en Keycloak. |
| `ChangeAccountPasswordUseCase` | `use_cases/change_password.py` | Cambia password e invalida sesión. |
| `RequestResetPasswordUseCase` | `use_cases/request_reset_password.py` | Genera token one-shot, lo cachea, manda email. |
| `ConfirmResetPasswordUseCase` | `use_cases/confirm_reset_password.py` | Consume el token (GETDEL) y resetea en Keycloak. |

Ports: `identity_provider`, `authentication_provider`, `account_repository`, `email_recipient_reader`, `profile_registration_writer`, `compensation_task`, `unit_of_work`.

## Registro — saga con compensación

`register` ejecuta una saga de dos sistemas (Keycloak + DB local) que no comparten transacción (ver [[adr-keycloak-saga-compensation]]):

1. `email_policy.ensure_email_available` — rechaza temprano si el email ya existe.
2. `idp.create_account(email, password)` → `kc_user_id` (UUID de Keycloak).
3. Crea `Account(account_id=kc_user_id, ...)` + perfil (`ProfileFactory.from_register`).
4. `uow.commit()`.

**Manejo de fallos** (todos hacen rollback de la DB primero):
- `IntegrityError` (email/cuenta duplicada en carrera): intenta `idp.delete_account(kc_user_id)`. Si el delete falla, **encola** un `KcCompensationTask`.
- `BaseError` o `Exception` genérica: encola directamente un `KcCompensationTask` para borrar el usuario de Keycloak.

Así nunca queda un usuario en Keycloak sin su `Account` local; si la limpieza inmediata falla, el worker la reintenta (ver [[users-service-kc-compensation]]).

## Sesiones — cookies

- **login**: `AuthenticateAccountUseCase.login` autentica contra Keycloak y `set_auth_cookies` setea `access_token` + `refresh_token`.
- **refresh**: toma el `refresh_token` de la cookie, pide nuevos tokens, re-setea cookies.
- **logout**: borra las cookies y revoca el refresh token en Keycloak (best-effort).
- **change-password**: tras cambiar, borra las cookies (fuerza re-login).

## Reset de contraseña — token de un solo uso

Dos pasos desacoplados por un token en Redis (ver [[adr-action-tokens-redis]]):

1. **Request** (`/auth/reset-password/request`):
   - Busca la cuenta por email; si no existe o no está activa, **retorna en silencio** (no filtra existencia).
   - Genera `secrets.token_urlsafe(32)`, guarda en Redis `{account_id}` bajo `reset_password_cache_key(hash_token(token))` con TTL.
   - Manda email (Brevo) con URL al frontend que incluye el token en query.
2. **Confirm** (`/auth/reset-password/confirm`, token vía Bearer):
   - Valida que `new_password == confirm_password`.
   - `getdel_json` del token (consumo atómico — un solo uso).
   - Carga la cuenta; si no está activa, retorna en silencio.
   - `idp.reset_password(account_id, new_password)` en Keycloak.

## Privacidad

Los endpoints de request (reset / reactivación) siempre responden 202 con mensaje genérico ("si la cuenta existe, se enviará un email") — no revelan si el email está registrado.

## Claims

- El registro crea primero el usuario en Keycloak y usa su UUID como `account_id` ([register_account.py:77-85](backend/users-service/src/app/services/auth/use_cases/register_account.py#L77-L85)).
- Si la persistencia falla, se intenta borrar el usuario de Keycloak; si ese borrado falla, se encola un `KcCompensationTask` ([register_account.py:98-138](backend/users-service/src/app/services/auth/use_cases/register_account.py#L98-L138)).
- El reset password guarda en Redis el `account_id` bajo el hash del token con TTL ([request_reset_password.py:34-41](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L34-L41)).
- Confirm consume el token con `getdel_json` (un solo uso) ([confirm_reset_password.py:59-67](backend/users-service/src/app/services/auth/use_cases/confirm_reset_password.py#L59-L67)).
- Request-reset retorna en silencio si la cuenta no existe o está inactiva ([request_reset_password.py:31-32](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L31-L32)).
- Change-password borra las cookies de auth tras el cambio ([account.py:97-99](backend/users-service/src/app/api/routes/account.py#L97-L99)).
- El token de reset es `secrets.token_urlsafe(32)` ([request_reset_password.py:34](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L34)).
