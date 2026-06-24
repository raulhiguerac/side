---
title: users-service
status: draft
last-verified: 2026-06-23
owners: [users-service]
related:
  - "[[architecture]]"
  - "[[users-service-architecture]]"
  - "[[users-service-auth]]"
  - "[[users-service-user]]"
  - "[[users-service-keycloak]]"
sources: [../../sources/users-service/2026-05-28-foundational-exploration.md, ../../sources/users-service/2026-06-23-public-profile-endpoint.md]
---

## TL;DR

Microservicio de **identidad y perfiles**: registro, login/refresh/logout, reset de contraseña, perfiles (persona/empresa), foto, onboarding e intereses, y ciclo de cuenta (deactivación/reactivación). **Único servicio que gestiona usuarios en Keycloak** (los demás solo validan JWT). Hex pattern con dos dominios (`auth`, `user`) sobre Postgres. Corre un worker de compensación in-process vía APScheduler.

## Por qué existe

Centraliza todo lo relacionado a la cuenta de un usuario:

1. **Auth** — puente con Keycloak para crear cuentas, autenticar (emite cookies) y resetear contraseñas. El resto del backend solo verifica el JWT resultante.
2. **Perfil** — datos de persona u organización, foto, descripción, score.
3. **Onboarding e intereses** — wizard de 4 pasos que captura intención y preferencias geográficas/de tipo de propiedad (alimenta el feed de [[properties-service]]).
4. **Ciclo de cuenta** — deactivación soft y reactivación por email.

## Dominios

| Dominio | Estado | Qué hace |
|---|---|---|
| `auth` | implementado | Registro (saga con Keycloak), login/refresh/logout, change password, reset password (request + confirm). |
| `user` | implementado | Cuenta (get, deactivate, reactivate), perfil (get/update/foto), onboarding (4 pasos), intereses. |

`services/shared/` aloja ports/adapters/policies comunes: `CachePort`, `EmailSender`, `StoragePort`, `AccountReader`, y políticas (`active_account_policy`, `account_email_availability_policy`).

## Public surface

Todo bajo prefijo `/v1`.

| Método | Path | Auth |
|---|---|---|
| POST | `/v1/auth/register` | público |
| POST | `/v1/auth/login` | público (setea cookies) |
| POST | `/v1/auth/refresh` | cookie refresh |
| POST | `/v1/auth/logout` | cookie refresh (opcional) |
| POST | `/v1/auth/change-password` | cookie access |
| POST | `/v1/auth/reset-password/request` | público |
| POST | `/v1/auth/reset-password/confirm` | Bearer (action token) |
| GET | `/v1/users/me` | cookie access |
| GET | `/v1/users/me/interests` | cookie access |
| GET/PATCH | `/v1/users/me/profile` | cookie access |
| GET | `/v1/users/profiles/{account_id}` | público (sin auth) |
| POST | `/v1/users/me/profile/photo` | cookie access |
| POST | `/v1/users/me/deactivate` | cookie access |
| POST | `/v1/users/reactivation/request` | público |
| POST | `/v1/users/reactivation/confirm` | Bearer (action token) |
| POST | `/v1/onboarding/{intent,city,neighborhood,property-type}` | cookie access |

## Consumers

- **frontend Vue**: registro, login, onboarding, perfil, foto. Recibe cookies HttpOnly.
- **Keycloak** (saliente): `users-service` crea/borra usuarios y resetea passwords vía admin client; autentica vía OpenID auth client.
- **Brevo** (saliente): emails transaccionales (reset password, reactivación).
- **Todos los demás microservicios** (indirecto): consumen los JWT que Keycloak emite a través del login de este servicio, pero no llaman a users-service directamente.

## Boundaries — lo que users-service **NO** hace

- **No es el store de identidad** — Keycloak es la fuente de verdad de credenciales; `accounts` es el espejo local con metadata de negocio.
- **No valida JWT de otros servicios** — cada servicio valida su propio token contra el JWKS de Keycloak.
- **No resuelve geografía** — el onboarding guarda IDs (`locality_id`, `neighborhood_id`) que vienen del frontend (vía [[catalog-service]]); no los valida contra catalog hoy.
- **No tiene comm async entre servicios** — el único trabajo en background es el worker de compensación de Keycloak (interno).

## Stack

- **FastAPI + Uvicorn** — HTTP layer (prefijo `/v1`)
- **SQLModel + Postgres** (imagen `postgres:17`, sin PostGIS) — DB `identity_service_db`
- **Keycloak** (`python-keycloak`) — IdP: admin client + OpenID auth client
- **Redis** — cache de cuenta/perfil + tokens de un solo uso (reset/reactivación)
- **MinIO / S3** (`boto3`) — fotos de perfil (upload a través del backend)
- **Brevo** (`brevo-python`) — emails transaccionales
- **APScheduler** — worker de compensación in-process
- **PyJWT** — validación de access token (cookie) en endpoints autenticados

## Roadmap inmediato

- [ ] Incluir el health router en `api_router` (existe pero no está montado)
- [ ] Validar IDs de onboarding contra catalog (hoy se confían del cliente)
- [ ] Política de limpieza de cuentas soft-deactivated antiguas

## Related

- [[architecture]] — monorepo, hex pattern, comunicación
- [[users-service-architecture]] — arquitectura interna
- [[users-service-auth]] — dominio auth (saga de registro, sesiones, reset)
- [[users-service-user]] — dominio user (perfil, onboarding, ciclo de cuenta)
- [[users-service-keycloak]] — integración con el IdP
- [[users-service-email-brevo]] — emails transaccionales
- [[users-service-kc-compensation]] — worker de compensación
- [[users-service-local-dev]] — runbook
- [[adr-auth-keycloak-jwt]] — decisión cross-service de auth

## Claims

- `users-service` define 2 dominios bajo `services/`: `auth` y `user`, más `shared` ([services/](backend/users-service/src/app/services)).
- El `api_router` incluye `account`, `user`, `onboarding` — no incluye health ([api/main.py:3-8](backend/users-service/src/app/api/main.py#L3-L8)).
- La app monta el router bajo el prefijo `/v1` ([main.py:33](backend/users-service/src/app/main.py#L33)).
- El servicio crea y borra usuarios en Keycloak vía `KeycloakAdminClient` ([admin_client.py:48-118](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py#L48-L118)).
- La sesión usa cookies (`access_token`, `refresh_token`); los action tokens usan Bearer header ([auth.py:45](backend/users-service/src/app/api/deps/auth.py#L45), [action_token.py:6-9](backend/users-service/src/app/api/deps/action_token.py#L6-L9)).
- El worker de compensación corre in-process vía APScheduler cada 900s ([scheduler.py:19-27](backend/users-service/src/app/core/scheduler.py#L19-L27)).
- La DB es `postgres:17` plano (`identity_service_db`), sin PostGIS ([docker-compose.yml:19-22](docker-compose.yml#L19-L22)).
