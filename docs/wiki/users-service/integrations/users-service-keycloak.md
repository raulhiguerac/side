---
title: Integración users → Keycloak
status: draft
last-verified: 2026-05-28
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-auth]]"
  - "[[adr-auth-keycloak-jwt]]"
  - "[[adr-keycloak-saga-compensation]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

users-service es el **único** servicio que gestiona usuarios en Keycloak. Usa **dos clientes** con secrets distintos: `KeycloakAdminClient` (crear/borrar usuario, set password — server-to-server) y `KeycloakAuthClient` (login/refresh/revoke — OpenID). El resto del backend solo valida los JWT que Keycloak emite.

## Dos clientes, dos roles

| Cliente | Archivo | Credencial | Operaciones |
|---|---|---|---|
| `KeycloakAdminClient` | `integrations/identity_provider/keycloak/admin_client.py` | `KC_CLIENT_ID` + `KC_ADMIN_SECRET` | `create_account_record`, `set_password`, `delete_account` |
| `KeycloakAuthClient` | `integrations/identity_provider/keycloak/auth_client.py` | `KC_CLIENT_AUTH` + `KC_AUTH_SECRET` | `keycloak_login`, `keycloak_refresh_token`, `keycloak_revoke_token` |

Ambos comparten `KEYCLOAK_URL` y `KC_REALM`. Cada uno falla en construcción con `IdentityProviderMisconfiguredError` si le falta alguna env var.

Los UCs no ven los clientes concretos: dependen de los ports `IdentityProvider` y `AuthenticationProvider`, implementados por los adapters `KeycloakIdp` y `KeycloakAuthProvider`.

## Identidad compartida

El `account_id` de la tabla `accounts` **es** el UUID que Keycloak genera al crear el usuario. No hay tabla de mapeo: el `sub` del JWT, el `account_id` local y el user-id de Keycloak son el mismo valor. Esto simplifica el join lógico entre el espejo local y el IdP.

## Traducción de errores

`get_keycloak_status(error)` extrae el status HTTP del error de `python-keycloak`. La convención:
- `status is None` o `>= 500` → `IdentityProviderUnavailableError` (problema del IdP, reintentar).
- `404` en delete → se trata como éxito idempotente (el usuario ya no existe).
- otros 4xx → error de dominio específico (`KeycloakRegisterError`, `KeycloakSetPasswordError`, `KeycloakDeleteAccountError`).

Esta distinción es la que permite al worker de compensación decidir si reintentar o marcar la task como fallida.

## Compensación

Como Keycloak y la DB local no comparten transacción, el registro usa una saga: si la DB falla tras crear el usuario en Keycloak, hay que borrarlo. El borrado inmediato puede fallar (IdP caído); en ese caso se encola un `KcCompensationTask` que el worker reintenta. Ver [[adr-keycloak-saga-compensation]] y [[users-service-kc-compensation]].

## Validación de JWT (lado consumidor)

Aunque users-service emite las sesiones, también valida sus propios access tokens en endpoints autenticados: `get_current_principal` usa `PyJWKClient` contra `KC_JWKS_URL` con `KC_ISSUER` y `OIDC_AUDIENCE`. Es el mismo patrón que el resto de servicios (ver `[[adr-auth-keycloak-jwt]]`), solo que acá el token viene de la cookie `access_token`.

## Claims

- `KeycloakAdminClient` requiere `KEYCLOAK_URL`, `KC_CLIENT_ID`, `KC_REALM`, `KC_ADMIN_SECRET` ([admin_client.py:20-38](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L20-L38)).
- `KeycloakAuthClient` requiere `KEYCLOAK_URL`, `KC_CLIENT_AUTH`, `KC_REALM`, `KC_AUTH_SECRET` ([auth_client.py:17-35](backend/users-service/src/app/integrations/identity_provider/keycloak/auth_client.py#L17-L35)).
- `create_account_record` crea el usuario con `enabled=True` y devuelve el UUID de Keycloak ([admin_client.py:48-61](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L48-L61)).
- `delete_account` trata un 404 como éxito idempotente ([admin_client.py:104-107](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L104-L107)).
- Errores con status None o >= 500 se mapean a `IdentityProviderUnavailableError` ([admin_client.py:64-67](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L64-L67)).
- El `set_password` usa `temporary=False` (password permanente) ([admin_client.py:80-85](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L80-L85)).
