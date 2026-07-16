---
title: Runbook — users-service local dev
status: draft
last-verified: 2026-07-15
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-architecture]]"
  - "[[users-service-keycloak]]"
  - "[[catalog-service-local-dev]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Workflow devcontainer-first como el resto. La infra (Keycloak + `users-ms-db` + Redis + MinIO) la levanta el compose. A mano: `cd backend/users-service && uv sync && migraciones + uvicorn`. **Keycloak debe estar configurado** con los dos clients (admin + auth) y sus secrets. El `.env.example` está casi completo, con dos trampas: la API key de Brevo y los dos secrets de Keycloak.

## Prerequisites

- Docker Desktop + VS Code con Dev Containers.
- Repo clonado y `.env` en el root.
- **Keycloak corriendo** con realm + dos clients configurados (uno admin con service account, uno de auth con direct grant).
- **MinIO** + bucket de fotos de perfil.
- Una **API key de Brevo** para probar emails (reset / reactivación).

## Servicios relevantes que levantan

| Servicio | Imagen | Para qué | Credenciales |
|---|---|---|---|
| `develop` | build local | El devcontainer | n/a |
| `users-ms-db` | `postgres:17` | DB `identity_service_db` | admin / admin |
| `keycloak` (+ `keycloak-db`) | keycloak:26.4.7 | IdP — admin UI en :8180 | admin / admin |
| `redis` | redis:latest | Cache + tokens one-shot | n/a |
| `minio` | minio | Fotos de perfil | ver compose |

## Correr users-service

```bash
cd /workspace/backend/users-service
uv sync
# crear .env del servicio — ver siguiente sección
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La app monta todo bajo `/v1`. Nota: el health router **no está incluido** en el router, así que no hay `/v1/health` hoy.

## Env vars del servicio

`backend/users-service/.env.example` declara casi todo. Set de referencia:

```bash
DATABASE_URL=postgresql://admin:admin@users-ms-db:5432/identity_service_db
REDIS_URL=redis://redis:6379/1

# Keycloak — dos clients
KEYCLOAK_URL=http://keycloak:8080
KC_REALM=master
KC_CLIENT_ID=<admin-client-id>        # client con service account (admin)
KC_ADMIN_SECRET=<admin-client-secret>
KC_CLIENT_AUTH=<auth-client-id>       # client de login (direct grant)
KC_AUTH_SECRET=<auth-client-secret>

# Validación de JWT (lado consumidor)
KC_JWKS_URL=http://keycloak:8080/realms/master/protocol/openid-connect/certs
KC_ISSUER=http://keycloak:8080/realms/master
OIDC_AUDIENCE=account

# Storage (MinIO)
PROFILE_PHOTOS_BUCKET=profile-photos
STORAGE_PUBLIC_BASE_URL=http://localhost:9000
ACCESS_KEY=<minio-access>
SECRET_KEY=<minio-secret>
MINIO_URL=http://minio:9000
ACCEPTED_IMAGE_MAX_SIZE=5242880
ACCEPTED_IMAGE_MIME_TYPES=image/jpeg,image/png

# Email (Brevo) — OJO con el nombre
BREVO_API_KEY=<brevo-key>             # el cliente lee BREVO_API_KEY, NO BREVO_SMTP_KEY

# Frontend (para los links de los emails)
FRONT_BASE_URL=http://localhost:8080
CACHE_REACTIVATION_TTL_SECONDS=900
```

### Trampas

- **`BREVO_API_KEY` vs `BREVO_SMTP_KEY`**: el `.env.example` declara `BREVO_SMTP_KEY`, pero el cliente lee `BREVO_API_KEY` ([client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15)). Setear `BREVO_API_KEY`.
- **Dos clients de Keycloak distintos**: `KC_CLIENT_ID`/`KC_ADMIN_SECRET` (admin) y `KC_CLIENT_AUTH`/`KC_AUTH_SECRET` (auth). No reusar el mismo client para ambos.
- **`FRONT_BASE_URL` es obligatorio** — el settings hace `raise RuntimeError` si falta ([settings.py:9-11](backend/users-service/src/app/core/config/settings.py#L9-L11)).

## Configurar Keycloak (primera vez)

1. Admin UI en http://localhost:8180 (admin/admin).
2. En el realm, crear un **client admin** con *Service accounts enabled* y rol `manage-users` del `realm-management`. Copiar su secret → `KC_ADMIN_SECRET`.
3. Crear un **client de auth** con *Direct access grants enabled*. Copiar su secret → `KC_AUTH_SECRET`.
4. Asegurar que `account` esté en el audience de los tokens (`OIDC_AUDIENCE=account`), o ajustar.

## Probar registro + login

```bash
# Registro (crea usuario en Keycloak + Account local)
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Secret123!","account_type":"person", ...}'

# Login (setea cookies access_token + refresh_token)
curl -i -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Secret123!"}'

# Endpoint autenticado (cookie)
curl http://localhost:8000/v1/users/me -b "access_token=<token-de-la-cookie>"
```

## Verificar el worker de compensación

El scheduler corre cada 15 min dentro del proceso. Para forzar una task de compensación: provocar un fallo de DB durante el registro (p. ej. apagar `users-ms-db` justo después de crear el usuario en Keycloak) y observar `kc_compensation_tasks`:

```bash
psql -h users-ms-db -U admin -d identity_service_db \
  -c "SELECT id, kc_user_id, status, attempts, next_retry_at FROM kc_compensation_tasks;"
```

## Known gaps (2026-05-28)

1. **Health router no montado** — `routes/health.py` existe pero `api_router` no lo incluye; no hay `/v1/health`.
2. **`BREVO_SMTP_KEY` en `.env.example`** no coincide con `BREVO_API_KEY` que lee el código.
3. **Onboarding no valida IDs contra catalog** — confía en los `locality_id`/`neighborhood_id` que manda el frontend.
4. **Sin limpieza de cuentas soft-deactivated** — quedan en DB indefinidamente.
5. **Setup de Keycloak manual** — los dos clients y sus roles se configuran a mano la primera vez.

## Comandos útiles

```bash
uv run pytest                          # 40 archivos de test
uv run alembic current                 # 6 migraciones disponibles
psql -h users-ms-db -U admin -d identity_service_db
docker exec -it $(docker ps -qf name=redis) redis-cli
> KEYS reset_password:*
docker logs $(docker ps -qf name=keycloak) -f
```

## Claims

- La DB es `postgres:17` (`identity_service_db`), sin PostGIS ([docker-compose.yml:19-24](docker-compose.yml#L19-L24)).
- El `.env.example` declara `BREVO_SMTP_KEY` pero el cliente lee `BREVO_API_KEY` ([backend/users-service/.env.example](backend/users-service/.env.example), [client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15)).
- `FRONT_BASE_URL` es obligatorio: el settings lanza `RuntimeError` si falta ([settings.py:9-11](backend/users-service/src/app/core/config/settings.py#L9-L11)).
- La app monta el router bajo `/v1` y no incluye el health router ([main.py:33](backend/users-service/src/app/main.py#L33), [api/main.py:3-8](backend/users-service/src/app/api/main.py#L3-L8)).
- Hay 6 migraciones y 40 archivos de test al 2026-05-28 ([migrations/versions/](backend/users-service/src/app/migrations/versions), [tests/](backend/users-service/tests)).
- Las dependencias clave: `apscheduler`, `python-keycloak`, `brevo-python`, `boto3`, `redis[hiredis]` ([pyproject.toml:7-31](backend/users-service/pyproject.toml#L7-L31)).
