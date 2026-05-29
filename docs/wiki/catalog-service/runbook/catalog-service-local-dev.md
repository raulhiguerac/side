---
title: Runbook — catalog-service local dev
status: draft
last-verified: 2026-05-28
owners: [catalog-service]
related: [[catalog-service]], [[catalog-service-architecture]], [[analytics-service-local-dev]]
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
---

## TL;DR

Mismo workflow devcontainer-first que [[analytics-service-local-dev]]: abrir el repo en VS Code → "Reopen in Container" → docker-compose levanta toda la infra (incluyendo `catalog-ms-db` con PostGIS). Después, a mano dentro del devcontainer: `cd backend/catalog-service && uv sync && correr migraciones + uvicorn`. Auth se prueba con **cookie** `access_token` (no header Bearer — distinto a analytics). El catálogo se siembra hoy manualmente vía bulk endpoints — sin script de seed.

## Prerequisites

- Docker Desktop corriendo.
- VS Code con extensión **Dev Containers**.
- Repo clonado.
- Archivo `.env` en el root (compartido con users-service hoy).
- **`MAPBOX_API_KEY`** propia para probar `/geo-resolution/resolve-neighborhood` (deprecado, ver [[adr-mapbox-frontend-only]]). No necesaria si solo vas a usar `/by-coordinates`.

## Levantar el entorno

1. Abrir el repo en VS Code.
2. Command palette → **Dev Containers: Reopen in Container**.
3. Primera vez compila el devcontainer + arranca todos los services. Tarda ~5-10 min.
4. `postCreateCommand` corre `setup-analytics-kernel.sh` (no afecta a catalog).

## Servicios relevantes que levantan

Subset del compose que necesita catalog-service:

| Servicio | Imagen | Host port | Para qué | Credenciales |
|---|---|---|---|---|
| `develop` | build local | 8000, 5173, 8080 | El devcontainer (tu shell) | n/a |
| `catalog-ms-db` | **`postgis/postgis:17-master`** | (interno) | DB de catalog (PostGIS; properties-ms-db también lo usa) | admin / admin |
| `keycloak-db` | postgres:17 | (interno) | DB de Keycloak | keycloak / password |
| `keycloak` | keycloak:26.4.7 | **8180** | IdP — admin UI en http://localhost:8180 | admin / admin |
| `redis` | redis:latest | 6379 | Cache forward geocode + lock + FetchZone short-circuit | n/a |
| `redisinsight` | redis/redisinsight | 5540 | UI de Redis | n/a |
| `mlflow`, `minio`, etc. | — | — | irrelevantes para catalog | — |

## Correr catalog-service

Dentro del devcontainer:

```bash
cd /workspace/backend/catalog-service
uv sync
# crear .env del servicio — ver siguiente sección
uv run alembic upgrade head     # aplicar migraciones
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/v1/health
```

## Env vars del servicio

`backend/catalog-service/.env.example` **está incompleto** al 2026-05-21 (igual que el de analytics): solo declara `DATABASE_URL` y `REDIS_URL`. Set mínimo recomendado para dev local:

```bash
# Persistencia (la DB que levanta el compose)
DATABASE_CATALOG_URL=postgresql://admin:admin@catalog-ms-db:5432/catalog_service_db
REDIS_URL=redis://redis:6379/3

# Auth (Keycloak del compose)
KC_JWKS_URL=http://keycloak:8080/realms/master/protocol/openid-connect/certs
KC_ISSUER=http://keycloak:8080/realms/master
OIDC_AUDIENCE=account
ADMIN_ROLE=admin

# Mapbox (solo necesario hasta el refactor de /geo-resolution; ver ADR-0005)
MAPBOX_API_KEY=<tu token>

# (los TTLs y H3_RESOLUTION tienen defaults razonables en settings.py)
```

Notas:
- **`DATABASE_CATALOG_URL`** (no `DATABASE_URL`) — el settings lo lee así específicamente ([core/config/settings.py:8](backend/catalog-service/src/app/core/config/settings.py#L8)).
- `KEYCLOAK` apunta al host interno del compose (`keycloak:8080`), no a `localhost:8180`. Los servicios resuelven nombres dentro de `dev-net`.
- Si `MAPBOX_API_KEY` falta, las requests a `/geo-resolution/resolve-neighborhood` fallan con `GeoResolutionMisconfiguredError`. El otro endpoint (`/by-coordinates`) **no** lo necesita.

## Probar `/v1/by-coordinates` end-to-end

Diferencia importante con analytics: **JWT viene en cookie, no header**. Por convención del servicio ([[catalog-service-architecture]] sección Auth).

### Obtener un token de Keycloak

```bash
TOKEN=$(curl -s -X POST \
  http://localhost:8180/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" \
  | jq -r .access_token)
```

### Llamar un endpoint público (sin auth)
```bash
curl http://localhost:8000/v1/countries
# Debería devolver [] si no hay seed
```

### Llamar un endpoint admin (con cookie)
```bash
curl -X POST http://localhost:8000/v1/admin/countries \
  -H "Content-Type: application/json" \
  -b "access_token=$TOKEN" \
  -d '{
    "iso_alpha2": "CO",
    "iso_alpha3": "COL",
    "iso_numeric": "170",
    "name": "Colombia",
    "phone_code": "+57",
    "currency_code": "COP",
    "default_timezone": "America/Bogota"
  }'
```

Si recibís `403 FORBIDDEN`: el user `admin` no tiene asignado el role `admin` en el realm. Ir al Keycloak admin UI (http://localhost:8180), realm `master`, Users → admin → Role Mappings → assign `admin`.

### Llamar reverse geocoding (no necesita auth ni Mapbox)
```bash
curl "http://localhost:8000/v1/geo-resolution/by-coordinates?lat=4.65&lon=-74.08"
# Devuelve LocationByCoordinates si hay un barrio con polígono que contiene el punto, 404 si no
```

## Seed inicial — manual hoy

No hay script de seed automático al 2026-05-21. Workflow manual:

1. Crear country `CO` (ejemplo arriba).
2. Crear admin_division `Cundinamarca` (POST `/v1/admin/admin-divisions`).
3. Crear locality `Bogotá D.C.` (POST `/v1/admin/localities`).
4. Bulk-create barrios desde CSV de IDECA:
   ```bash
   curl -X POST "http://localhost:8000/v1/admin/localities/<locality_id>/neighborhoods/bulk" \
     -b "access_token=$TOKEN" \
     -F "file=@barrios_ideca.csv"
   ```
5. Bulk-enrich con GeoJSON de polígonos IDECA:
   ```bash
   curl -X POST "http://localhost:8000/v1/admin/localities/<locality_id>/neighborhoods/bulk/geometry?name_field=nombre" \
     -b "access_token=$TOKEN" \
     -F "file=@barrios_ideca.geojson"
   ```

Los CSVs/GeoJSON de IDECA viven hoy localmente — pedirlos al equipo si no los tenés. Mismos archivos que usa training del AVM.

**Futuro deseado** (ver Open items): side-container que corre estos pasos al startup leyendo desde un volumen montado o desde MinIO.

## Known gaps (2026-05-21)

1. **`.env.example` incompleto** — falta declarar `DATABASE_CATALOG_URL` (no `DATABASE_URL` — naming distinto), las 4 vars de Keycloak, `ADMIN_ROLE`, y `MAPBOX_API_KEY`.
2. **Sin script de seed** — todo manual vía bulk endpoints. Workflow no auto-recoverable si reseteás el volumen de Postgres.
3. **Role `admin` no auto-asignado al user `admin`** del realm — hay que setearlo a mano la primera vez.
4. **Bucket `mlflow-artifacts` y MinIO no son necesarios para catalog** — pero levantan igual con el compose (overhead aceptable para dev unificado).
5. **`MAPBOX_API_KEY` requerido por el endpoint legacy** — eliminable cuando se haga el refactor de [[adr-mapbox-frontend-only]].
6. **`FetchZone` refresh batch no existe** — zonas stale no se refrescan solas; solo en próximo georef. Manual hoy si necesitás re-fetchear: borrar la fila de `FetchZone` y volver a georefferenciar la zona.
7. **`h3_cells` lazy-fill se popula pero no acelera reads** — gap descrito en [[catalog-service-poi-lifecycle]] sección "lazy-fill".

## Comandos útiles dentro del devcontainer

```bash
# Re-sync deps después de cambios en pyproject.toml
uv sync

# Correr tests
uv run pytest

# Ver migraciones aplicadas
uv run alembic current

# Crear migración nueva
uv run alembic revision --autogenerate -m "describe change"

# Conectarse a la DB de catalog
psql -h catalog-ms-db -U admin -d catalog_service_db

# Inspeccionar Redis (UI gráfica en http://localhost:5540, host=redis port=6379)
docker exec -it $(docker ps -qf name=redis) redis-cli
> KEYS geo:*
> KEYS catalog:*

# Ver POIs cached para una zona específica
> GET geo:fetch_zone:<h3_index>

# Ver el log del Keycloak si auth falla
docker logs $(docker ps -qf name=keycloak) -f
```

## Claims

- catalog-service usa `postgis/postgis:17-master`; properties-service también la usa para su DB ([docker-compose.yml:31](docker-compose.yml#L31), [docker-compose.yml:42](docker-compose.yml#L42)).
- El servicio lee la connection string desde `DATABASE_CATALOG_URL` (no `DATABASE_URL`) ([core/config/settings.py:8](backend/catalog-service/src/app/core/config/settings.py#L8)).
- Auth lee JWT desde la cookie `access_token`, no del header `Authorization` ([api/deps/auth.py:45](backend/catalog-service/src/app/api/deps/auth.py#L45)).
- El `.env.example` del servicio solo declara `DATABASE_URL` y `REDIS_URL`, falta el resto ([backend/catalog-service/.env.example](backend/catalog-service/.env.example)).
- 2 migraciones Alembic disponibles al 2026-05-21 (catálogo geo + POIs) ([backend/catalog-service/src/app/migrations/versions/](backend/catalog-service/src/app/migrations/versions/)).
- No hay script de seed automatizado — el catálogo se carga vía bulk endpoints manualmente.
- El role `admin` debe asignarse a mano al user `admin` del realm `master` para que `/admin/*` pase `require_admin`.
- Postman collection / Insomnia para este flujo: pendiente.
