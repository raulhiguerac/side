---
title: Arquitectura interna de users-service
status: draft
last-verified: 2026-05-28
owners: [users-service]
related:
  - "[[architecture]]"
  - "[[users-service]]"
  - "[[users-service-auth]]"
  - "[[users-service-user]]"
  - "[[users-service-keycloak]]"
  - "[[users-service-kc-compensation]]"
sources: [../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Hex pattern con dos dominios (`auth`, `user`) + `shared`. Tres capas: `api/` (HTTP + DI + cookies), `services/<domain>/` (use cases + ports + adapters + policies + schemas), `integrations/` (Keycloak, Brevo, MinIO, Redis). Persistencia SQLModel a Postgres. Worker de compensación in-process vía APScheduler en el lifespan de FastAPI.

## Layout

```
src/app/
├── api/
│   ├── deps/
│   │   ├── auth.py                 # get_current_principal (cookie), refresh token deps
│   │   ├── action_token.py         # Bearer para reset/reactivación
│   │   ├── auth_use_cases.py       # DI dominio auth
│   │   ├── user_use_cases.py       # DI dominio user
│   │   ├── onboarding_use_cases.py # DI onboarding
│   │   ├── upload_validation.py    # valida MIME/size de foto
│   │   └── db.py, storage.py
│   ├── http/cookies.py             # set/delete auth cookies
│   ├── handlers/exception_handlers.py
│   ├── middleware/correlation_id.py
│   └── routes/{account,user,onboarding,health}.py
├── core/
│   ├── config/settings.py          # FRONT_BASE_URL, TTLs
│   ├── exceptions/                 # base, auth, account, user, identity_provider, email, storage, cache, validation
│   ├── files/{policies,validators}.py  # validación de uploads
│   ├── scheduler.py                # APScheduler lifespan → worker
│   ├── security.py
│   └── logging/
├── integrations/
│   ├── identity_provider/keycloak/{admin_client,auth_client}.py
│   ├── email/brevo/client.py
│   ├── storage/minio/storage.py
│   └── cache/redis/cache.py
├── models/{account,interests,onboarding,kc_tasks}.py
├── schemas/{base,common}.py        # Principal
├── services/
│   ├── auth/                       # registro, sesiones, passwords
│   ├── user/                       # cuenta, perfil, onboarding, intereses
│   └── shared/                     # ports/adapters/policies comunes
└── workers/keycloak_tasks.py       # job de compensación
```

## Modelo de datos

| Tabla | Archivo | Rol |
|---|---|---|
| `accounts` | account.py | Espejo local del usuario de Keycloak. `account_id` = UUID de Keycloak. Email, tipo, `onboarding_step`, `is_active` + metadata de deactivación. |
| `user_profile` | account.py | Perfil de persona (1:1, FK cascade). Nombre, teléfono, intent, foto, score. |
| `company_profile` | account.py | Perfil de organización (1:1, FK cascade). |
| `user_consents` | account.py | Consentimientos (terms, marketing). |
| `onboarding_completions` | onboarding.py | PK compuesta `(account_id, key)` — registra cada paso completado. |
| `user_interest` | interests.py | Interés por ciudad (único por `(account_id, city_id)`). |
| `user_neighborhood_interest` | interests.py | Barrios rankeados 1-5 dentro de un interés de ciudad. |
| `user_property_type_interest` | interests.py | Tipo de propiedad por interés de ciudad. |
| `kc_compensation_tasks` | kc_tasks.py | Cola de compensación para borrar usuarios de Keycloak huérfanos. |

`account_id` es **el mismo UUID** que el `sub` del JWT de Keycloak — no hay mapeo, la identidad es compartida.

## Dominio `auth`

Registro (saga con Keycloak + compensación), login/refresh/logout (cookies), change password, reset password (request + confirm con token de un solo uso). Ver [[users-service-auth]].

## Dominio `user`

Cuenta (get/deactivate/reactivate), perfil (get/update/foto), onboarding (4 pasos), intereses. Lecturas de perfil con cache-aside vía orquestador. Ver [[users-service-user]].

## Dominio `shared`

- Ports: `AccountReader`, `CachePort`, `EmailSender`, `StoragePort`.
- Adapters: `RedisCacheAdapter`, `BrevoEmailSenderAdapter`, `MinioStorageAdapter`, `SqlAccountReader`.
- Policies: `AccountEmailAvailabilityPolicy` (email único al registrar), `ActiveAccountPolicy`.
- Helpers: `security.hash_token`, `url_builder` (redirect/public URLs).

## Integraciones

| Integración | Cliente(s) | Uso |
|---|---|---|
| **Keycloak** | `KeycloakAdminClient`, `KeycloakAuthClient` | Gestión de usuarios + autenticación. Ver [[users-service-keycloak]]. |
| **Redis** | `CacheClient` | Cache de cuenta/perfil + tokens de un solo uso. |
| **MinIO / S3** | `StorageClient` (boto3) | Fotos de perfil (upload directo a través del backend). |
| **Brevo** | `BrevoClient` | Emails transaccionales. Ver [[users-service-email-brevo]]. |

## Auth y sesiones

- **Sesión**: `get_current_principal` lee la cookie `access_token`, valida el JWT contra el JWKS de Keycloak (`PyJWKClient`), cachea el `Principal` en `request.state`. `refresh_token` también va en cookie.
- **Cookies**: `api/http/cookies.py` setea/borra ambas en login/refresh/logout/change-password.
- **Action tokens**: reset-password-confirm y reactivation-confirm reciben el token vía **Bearer header** (`HTTPBearer`), no cookie — son one-shot, no sesiones.
- A diferencia de properties/catalog, el `Principal` lleva `scope` (de `claims.scope`), no `roles`.

## Worker de compensación

`core/scheduler.py` arranca un `AsyncIOScheduler` en el lifespan de FastAPI que corre `run_job` cada 900s. El job (`workers/keycloak_tasks.py`) procesa `kc_compensation_tasks` pendientes para borrar usuarios de Keycloak que quedaron huérfanos tras un registro fallido. In-process, no proceso separado. Ver [[users-service-kc-compensation]] y `[[adr-apscheduler-in-process-worker]]`.

## Errores y exception handling

Jerarquía amplia en `core/exceptions/`: `base`, `auth`, `account`, `user`, `identity_provider`, `email`, `storage`, `cache`, `validation`. Los errores de Keycloak se traducen vía `translate_keycloak_error` / `get_keycloak_status` (distingue 4xx de 5xx → `IdentityProviderUnavailableError`). Los errores SQL vía `DbErrorTranslator`.

## Claims

- `account_id` de `accounts` es el UUID generado por Keycloak (se usa como PK) ([register_account.py:77-84](backend/users-service/src/app/services/auth/use_cases/register_account.py#L77-L84)).
- Hay 9 tablas: accounts, user_profile, company_profile, user_consents, onboarding_completions, user_interest, user_neighborhood_interest, user_property_type_interest, kc_compensation_tasks ([models/](backend/users-service/src/app/models)).
- `user_neighborhood_interest.interest_rank` está acotado a 1-5 por `CheckConstraint` ([interests.py:66](backend/users-service/src/app/models/interests.py#L66)).
- El `Principal` lleva `scope` extraído de `claims.scope`, no roles ([auth.py:94-102](backend/users-service/src/app/api/deps/auth.py#L94-L102)).
- Hay dos clientes Keycloak: `KeycloakAdminClient` (admin secret) y `KeycloakAuthClient` (auth client secret) ([admin_client.py:18-46](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L18-L46), [auth_client.py:15-43](backend/users-service/src/app/integrations/identity_provider/keycloak/auth_client.py#L15-L43)).
- El scheduler se inicia en el lifespan de la app y se apaga al cerrar ([scheduler.py:11-33](backend/users-service/src/app/core/scheduler.py#L11-L33)).
- Hay 6 migraciones Alembic y 40 archivos de test al 2026-05-28 ([migrations/versions/](backend/users-service/src/app/migrations/versions), [tests/](backend/users-service/tests)).
