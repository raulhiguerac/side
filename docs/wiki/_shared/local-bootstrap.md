---
title: Bootstrap del entorno local
status: stable
last-verified: 2026-09-27
owners: [_shared]
related:
  - "[[dev-workflow]]"
  - "[[architecture]]"
  - "[[adr-dev-config-versioned-artifacts-in-r2]]"
  - "[[adr-infra-reconciled-by-init-jobs]]"
  - "[[adr-seaweedfs-dev-object-storage]]"
  - "[[users-service-local-dev]]"
  - "[[catalog-service-local-dev]]"
  - "[[properties-service-local-dev]]"
  - "[[analytics-service-local-dev]]"
sources:
  - ../../sources/_shared/2026-09-07-entorno-dev-migrable.md
  - ../../sources/_shared/2026-09-27-minio-a-seaweedfs-y-rclone.md
---

## TL;DR

`make bootstrap && make up` levanta la infra en una maquina limpia; el unico
requisito del host es Docker. Por ahora las apps y los seeds estan comentados en el
compose y se corren a mano en el devcontainer. Siete valores viajan a mano en `.env.local`;
todo lo demas o esta versionado o lo baja `make bootstrap` desde Cloudflare R2.

## Topologia

El compose define 17 services activos en dos grupos, mas un tercero comentado:

| Grupo | Services |
|---|---|
| Infra | 5 Postgres (`catalog-ms-db` y `properties-ms-db` construidos desde `infra/postgis`), `keycloak`, `redis`, `redisinsight`, `minio` (SeaweedFS), `mlflow`, `kafka-broker`, `router` (ORS), `develop` |
| One-shots | `minio-init`, `keycloak-init`, `topic-init`, `mlflow-init` |
| Comentados | `users` (8000), `catalog` (8001), `properties` (8002), `analytics` (8003), `frontend` (8080), `seed-db`, `seed-dev-user` |

Por ahora los servers y el front se levantan a mano dentro del devcontainer
(`develop`), y VS Code reenvia sus puertos al host via `forwardPorts`. Los bloques
comentados siguen en el compose: al reactivarlos, cada MS vuelve a correr con el
codigo montado, `uvicorn --reload` y un entrypoint
([service-entrypoint.sh](infra/dev/service-entrypoint.sh)) que aplica `alembic
upgrade head` antes de levantar.

El encadenamiento es por healthcheck, no por `sleep`: 10 de los 17 services
declaran uno, y las dependencias usan `service_healthy` o
`service_completed_successfully`.

## Que viaja y como

| Origen | Contenido |
|---|---|
| git | Config determinista de dev (`backend/<svc>/.env.dev`, `frontend/.env.development`), el realm de Keycloak, los permisos S3 (`infra/seaweedfs/s3.json`), los scripts de init |
| `.env.local` (gitignoreado) | Siete valores: 4 de Cloudflare R2 + Mapbox, Brevo y Google Maps |
| R2 `runtime/` (~85 MB) | El `.pbf` de Bogota, los dumps de seed y el modelo AVM con su registro |
| R2 `datasets/` (~480 MB) | Scrape y CSVs de entrenamiento. Opcional, `make data-pull` |

Las rutas dentro de `runtime/` espejan las del repo, asi que el pull es un
`rclone copy` directo sin logica de mapeo. Ver
[[adr-dev-config-versioned-artifacts-in-r2]] para el porque de cada corte.

Los grafos de ORS **no** viajan: se reconstruyen desde el `.pbf` en ~145 s, y ORS
detecta un `.pbf` cambiado comparando su tamano en bytes contra el `stamp.txt` de
cada perfil.

## Los one-shots

Todos idempotentes, todos con centinela. Ver
[[adr-infra-reconciled-by-init-jobs]] para el patron.

- **`minio-init`** — crea los 4 buckets con `rclone mkdir`. El storage es
  SeaweedFS aunque el servicio se siga llamando `minio`; los usuarios y sus
  permisos no los crea el init, se declaran en
  [infra/seaweedfs/s3.json](infra/seaweedfs/s3.json). Ver
  [[adr-seaweedfs-dev-object-storage]].
- **`keycloak-init`** — fija los client secrets de `users-ms-admin` y
  `users-ms-auth`, que el export del realm enmascara como `**********`.
- **`seed-db`** (comentado por ahora) — restaura los 4 dumps saltando las tablas que ya tienen filas.
  Espera a que los servicios esten healthy porque los dumps son `--data-only`.
- **`seed-dev-user`** (comentado por ahora) — crea `dev@example.com` llamando a `POST /v1/auth/register`
  y le asigna el rol `admin`. No hace INSERT: `accounts.account_id` tiene que ser
  el `sub` que asigna Keycloak, y ese invariante vive en `RegisterAccountUseCase`.
  Por eso `keycloak-init` **no** puede pre-crear ese usuario.
- **`mlflow-init`** — copia el registro al volumen y sube los artifacts a
  `s3://mlflow-artifacts/3/` con `rclone copy`, antes de que arranque el server
  porque el backend store es sqlite. Valida con `rclone check` que no falte
  ningun archivo.

## Guardas del Makefile

`bootstrap` depende de `check-env` y `up` de `check-artifacts`. Fallan temprano y
con el comando de arreglo, porque el modo de falla alternativo es peor: ORS
levantando a medias o `seed-db` sin encontrar los dumps, varios minutos despues.

rclone corre en contenedor con `--user $(id -u)`, asi que el host no instala nada y
los archivos bajados no quedan con owner root. No es `mc`: `mc mirror` pide el
listado con `metadata=true`, que R2 no implementa, y transfiere 0 B.

## Claims

- `make bootstrap` exige `.env.local` con las 4 claves de R2 y aborta con el comando de arreglo si falta ([Makefile](Makefile)).
- `make up` aborta si falta el `.pbf`, los dumps de seed o el registro de MLflow ([Makefile](Makefile)).
- El compose define 17 services activos, de los cuales 4 son one-shots y 10 declaran healthcheck; las apps y los seeds estan comentados ([docker-compose.yml](docker-compose.yml)).
- `service-entrypoint.sh` corre `alembic upgrade head` antes de uvicorn; hoy no lo monta ningun service activo ([service-entrypoint.sh](infra/dev/service-entrypoint.sh)).
- `develop` no publica puertos; las apps que corren dentro llegan al host via `forwardPorts` ([devcontainer.json](.devcontainer/devcontainer.json)).
- Los grafos de ORS se reconstruyen desde el `.pbf` y cada perfil guarda en `stamp.txt` el tamano en bytes del `.pbf` con el que se construyo.
- `seed-dev-user` crea el usuario por `POST /v1/auth/register`, no por INSERT ([seed-dev-user.py](infra/dev/seed-dev-user.py)).
- `minio-init` y `mlflow-init` usan la imagen `rclone/rclone:1.75.1`; ninguno depende de `mc` ([docker-compose.yml](docker-compose.yml)).
- En el host, SeaweedFS publica S3 en `:9000` y la UI del filer en `:8888`, y MLflow en `:5050` porque macOS ocupa el 5000 con AirPlay Receiver ([docker-compose.yml](docker-compose.yml)).
- El volumen de rclone en el Makefile se monta desde `$(CURDIR)`, no desde `$(PWD)` ([Makefile](Makefile)).
