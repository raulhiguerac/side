# side

Marketplace inmobiliario. Monorepo con cuatro microservicios Python/FastAPI
(hexagonal), un frontend Vue 3 y el AVM en `data/ml/`.

La documentación viva está en [`docs/wiki/`](docs/wiki/) — arquitectura,
dominios, ADRs y runbooks por servicio.

## Levantarlo

El único requisito del host es **Docker**. Todo lo demás corre en contenedores.

```bash
git clone git@github.com:raulhiguerac/side.git && cd side

cp .env.local.example .env.local   # completá los 7 valores (ver abajo)
make bootstrap                     # baja ~85 MB de R2: pbf, seeds y modelo AVM
make up
```

El primer arranque tarda **10-15 minutos**: construye cinco imágenes, reconstruye
los grafos de ORS desde el `.pbf` (~2,5 min) y aplica migraciones y seeds. Los
siguientes son de segundos.

```bash
make          # lista todos los comandos
```

### Los 7 valores de `.env.local`

Es lo único que viaja a mano entre máquinas, y no puede automatizarse: la
credencial que baja los artefactos no puede vivir dentro de los artefactos.

| Variable | De dónde sale |
|---|---|
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | Cloudflare R2 |
| `MAPBOX_API_KEY` | Mapbox |
| `BREVO_API_KEY` | Brevo |
| `VUE_APP_GMAPS_KEY` | Google Cloud Console |

Todo lo demás —contraseñas de Postgres, secrets de Keycloak, claves de MinIO— es
determinista, vive en `backend/<servicio>/.env.dev` y está versionado a propósito:
son valores de `localhost` y fijarlos es lo que hace el entorno reproducible.

## Qué corre y dónde

| | URL | Credenciales |
|---|---|---|
| users-service | http://localhost:8000/docs | |
| catalog-service | http://localhost:8001/docs | |
| properties-service | http://localhost:8002/docs | |
| analytics-service | http://localhost:8003/docs | |
| frontend | http://localhost:8080 | |
| Keycloak | http://localhost:8180 | `admin` / `admin` |
| MinIO | http://localhost:9001 | `minioadmin` / `minioadmin` |
| MLflow | http://localhost:5000 | |
| RedisInsight | http://localhost:5540 | |
| ORS | http://localhost:8082/ors | |

**Usuario de dev:** `dev@example.com` / `dev12345`, con rol `admin`. Lo crea
`seed-dev-user` llamando al endpoint de registro real, así que su fila en
`accounts` y su usuario de Keycloak comparten id.

## Qué vive en R2 y por qué

El repo no lleva binarios ni datos. `make bootstrap` los trae:

| Destino | Qué |
|---|---|
| `infra/ors/files/` | Extracto OSM de Bogotá (18 MB) |
| `infra/seeds/` | Dumps de catálogo geo, POIs, properties y cuentas (16 MB) |
| `infra/mlflow/` | Modelo AVM y registro de MLflow (49 MB) |

Los grafos de ORS **no** viajan: se reconstruyen solos desde el `.pbf`, y ORS
detecta un `.pbf` cambiado comparando su tamaño en bytes.

`make data-pull` baja aparte los ~480 MB de scrape y CSVs de entrenamiento, que
solo hacen falta para reentrenar el AVM.

## Trabajar en un servicio

Los cinco corren en el compose con el código montado y hot-reload: editás en el
host y el proceso recarga. Para debuggear uno a mano, paralo y corrélo desde el
devcontainer:

```bash
docker compose stop catalog
cd backend/catalog-service && uv sync
PYTHONPATH=src uv run uvicorn app.main:app --reload --port 8001
```

Ojo: properties-service llama a catalog y users por hostname de red
(`http://catalog:8001`). Si parás uno para correrlo a mano, el otro deja de
resolverlo — corré los dos a mano, o ninguno.

## Empezar de cero

```bash
make reset   # DESTRUCTIVO: borra las 5 bases, MinIO, MLflow y los grafos
```

Lo que vive en R2 se recupera con `make bootstrap`. Lo que no, se pierde.
