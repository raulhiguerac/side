---
title: Runbook — properties-service local dev
status: draft
last-verified: 2026-05-28
owners: [properties-service]
related:
  - "[[properties-service]]"
  - "[[properties-service-architecture]]"
  - "[[catalog-service-local-dev]]"
  - "[[analytics-service-local-dev]]"
sources: [../../../sources/properties-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Mismo workflow devcontainer-first que [[catalog-service-local-dev]]: abrir el repo en VS Code → "Reopen in Container" → docker-compose levanta la infra (incluyendo `properties-ms-db` con PostGIS). Después, a mano: `cd backend/properties-service && uv sync && migraciones + uvicorn`. Auth por **cookie** `access_token`. Necesita catalog-service corriendo (con seed geo) para crear listings, y MinIO para el flujo de imágenes.

## Prerequisites

- Docker Desktop corriendo.
- VS Code con extensión **Dev Containers**.
- Repo clonado y `.env` en el root.
- **catalog-service corriendo y con seed geo** — sin barrios/ciudades válidos no se pueden crear listings.
- **MinIO** + bucket de fotos para el flujo de imágenes.

## Servicios relevantes que levantan

Subset del compose que necesita properties-service:

| Servicio | Imagen | Para qué | Credenciales |
|---|---|---|---|
| `develop` | build local | El devcontainer (tu shell) | n/a |
| `properties-ms-db` | **`postgis/postgis:17-master`** | DB de properties | admin / admin |
| `catalog-ms-db` + catalog | postgis | Dependencia geo (write time) | admin / admin |
| `keycloak` (+ db) | keycloak:26.4.7 | IdP — admin UI en :8180 | admin / admin |
| `redis` | redis:latest | Cache de detalle/feed/mapa/batch | n/a |
| `minio` | minio | Object storage de fotos | ver compose |

## Correr properties-service

Dentro del devcontainer:

```bash
cd /workspace/backend/properties-service
uv sync
# crear .env del servicio — ver siguiente sección
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

## Env vars del servicio

`backend/properties-service/.env.example` **está incompleto** al 2026-05-28: solo declara `DATABASE_URL` y `REDIS_URL`. Set mínimo recomendado para dev local:

```bash
# Persistencia (la DB que levanta el compose)
DATABASE_URL=postgresql://admin:admin@properties-ms-db:5432/properties-ms-db
REDIS_URL=redis://redis:6379/2

# Auth (Keycloak del compose)
KC_JWKS_URL=http://keycloak:8080/realms/master/protocol/openid-connect/certs
KC_ISSUER=http://keycloak:8080/realms/master
OIDC_AUDIENCE=account
ADMIN_ROLE=admin

# Dependencia geo
CATALOG_URL=http://catalog:8000

# Storage (MinIO)
BUCKET_PHOTOS_PROPERTIES=properties-photos
STORAGE_PUBLIC_BASE_URL=http://localhost:9000
# + credenciales boto3 (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / endpoint)

# (los TTLs, FEED_* y MAX_IMAGES_PER_PROPERTY tienen defaults en settings.py)
```

Notas:
- **`DATABASE_URL`** (plano, no `DATABASE_PROPERTIES_URL`) — el settings lo lee así ([core/config/settings.py:7](backend/properties-service/src/app/core/config/settings.py#L7)).
- `CATALOG_URL` se lee directo de env en `CatalogClient.__init__`, no vía settings — si falta, el cliente falla al construirse.
- Keycloak apunta al host interno del compose (`keycloak:8080`), no a `localhost:8180`.

## Probar create-property end-to-end

JWT viene en **cookie**, no header. Necesitás un barrio válido en catalog primero.

```bash
# 1. Obtener token de Keycloak
TOKEN=$(curl -s -X POST \
  http://localhost:8180/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" -d "username=admin" -d "password=admin" \
  -d "grant_type=password" | jq -r .access_token)

# 2. Conseguir un neighborhood_id + city_id válidos de catalog
curl "http://localhost:8000/v1/neighborhoods/by-localities?locality_ids=<locality_id>"

# 3. Crear la propiedad (cookie access_token)
curl -X POST http://localhost:8000/properties \
  -H "Content-Type: application/json" \
  -b "access_token=$TOKEN" \
  -d '{
    "property_type": "apartment", "listing_type": "sale",
    "condition": "used", "currency": "COP",
    "floor_number": 5, "area_m2": 80.0,
    "bedrooms": 3, "bathrooms": 2.0, "parking_spots": 1,
    "price": 450000000,
    "location": {
      "neighborhood_id": "<nb_id>", "city_id": "<city_id>",
      "country_id": "<country_id>", "latitude": 4.65, "longitude": -74.08
    }
  }'
```

La propiedad nace en `draft` — no aparece en `/search/feed` hasta que un admin la pase a `active` (`PATCH /admin/properties/{id}/status`).

## Flujo de imágenes

```bash
# 1. Pedir URLs presignadas
curl -X POST http://localhost:8000/properties/images/presigned-urls \
  -b "access_token=$TOKEN" -H "Content-Type: application/json" \
  -d '{"property_id": "<id>", "create_count": 3}'
# → { batch_id, items: [{ upload_url, public_url, key }] }

# 2. Subir cada archivo con PUT directo a upload_url (a MinIO, no al backend)
curl -X PUT "<upload_url>" --upload-file foto.jpg

# 3. Confirmar
curl -X POST http://localhost:8000/properties/<id>/images/confirm \
  -b "access_token=$TOKEN" -H "Content-Type: application/json" \
  -d '{"batch_id": "<batch_id>", "confirmed_keys": ["<key1>", "<key2>"]}'
```

## Known gaps (2026-05-28)

1. **`.env.example` incompleto** — solo `DATABASE_URL` y `REDIS_URL`; faltan Keycloak, `CATALOG_URL`, las de MinIO, y `ADMIN_ROLE`.
2. **Dependencia dura de catalog con seed** — no se puede crear listing sin un barrio válido; si catalog no está sembrado, create falla con error de location.
3. **Path ML de precio estimado huérfano** — sin worker que consuma `price-predicted`; `ml_estimated_price` solo se puede escribir manualmente invocando el UC sin principal.
4. **Role `admin` no auto-asignado** al user `admin` del realm — setearlo a mano para `/admin/*`.
5. **MinIO bucket no auto-creado** — crear `BUCKET_PHOTOS_PROPERTIES` a mano la primera vez.
6. **Seed de propiedades** — vía `/admin/properties/bulk` (requiere catalog para geo-enrichment); no hay script automático.

## Comandos útiles

```bash
uv run pytest                      # tests (13 archivos de test unit)
uv run alembic current             # migración aplicada
psql -h properties-ms-db -U admin -d properties-ms-db
docker exec -it $(docker ps -qf name=redis) redis-cli
> KEYS properties:*
> KEYS feed:*
> KEYS map:h3:*
```

## Claims

- properties-service usa la imagen `postgis/postgis:17-master` para `properties-ms-db` ([docker-compose.yml:41-42](docker-compose.yml#L41-L42)).
- El servicio lee la connection string desde `DATABASE_URL` (plano) ([core/config/settings.py:7](backend/properties-service/src/app/core/config/settings.py#L7)).
- `CATALOG_URL` se lee directamente de env en el constructor de `CatalogClient`, no vía settings ([catalog_client.py:12-14](backend/properties-service/src/app/integrations/catalog/catalog_client.py#L12-L14)).
- Auth lee el JWT desde la cookie `access_token` ([api/deps/auth.py:46](backend/properties-service/src/app/api/deps/auth.py#L46)).
- El `.env.example` solo declara `DATABASE_URL` y `REDIS_URL` ([backend/properties-service/.env.example](backend/properties-service/.env.example)).
- Hay 13 archivos de test unit bajo `tests/unit/` al 2026-05-28 ([backend/properties-service/tests/](backend/properties-service/tests)).
- El servicio se arranca con `uvicorn app.main:app` en el Dockerfile ([backend/properties-service/Dockerfile](backend/properties-service/Dockerfile)).
