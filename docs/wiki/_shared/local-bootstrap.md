---
title: Bootstrap del entorno local
status: stable
last-verified: 2026-09-07
owners: [_shared]
related:
  - "[[dev-workflow]]"
  - "[[architecture]]"
  - "[[adr-dev-config-versioned-artifacts-in-r2]]"
  - "[[adr-infra-reconciled-by-init-jobs]]"
  - "[[users-service-local-dev]]"
  - "[[catalog-service-local-dev]]"
  - "[[properties-service-local-dev]]"
  - "[[analytics-service-local-dev]]"
sources:
  - ../../sources/_shared/2026-09-07-entorno-dev-migrable.md
---

## TL;DR

`make bootstrap && make up` levanta el monorepo entero en una maquina limpia; el
unico requisito del host es Docker. Siete valores viajan a mano en `.env.local`;
todo lo demas o esta versionado o lo baja `make bootstrap` desde Cloudflare R2.

## Topologia

El compose define 24 services en tres grupos:

| Grupo | Services |
|---|---|
| Aplicaciones | `users` (8000), `catalog` (8001), `properties` (8002), `analytics` (8003), `frontend` (8080) |
| Infra | 5 Postgres, `keycloak`, `redis`, `redisinsight`, `minio`, `mlflow`, `kafka-broker`, `router` (ORS), `develop` |
| One-shots | `minio-init`, `keycloak-init`, `topic-init`, `seed-db`, `seed-dev-user`, `mlflow-init` |

Los cuatro MS corren con el codigo montado y `uvicorn --reload`, y su entrypoint
([service-entrypoint.sh](infra/dev/service-entrypoint.sh)) aplica `alembic upgrade
head` antes de levantar. El devcontainer (`develop`) sigue existiendo para
trabajar adentro, pero ya no publica puertos: los toman los servicios, y VS Code
los reenvia via `forwardPorts`.

El encadenamiento es por healthcheck, no por `sleep`: 14 de los 24 services
declaran uno, y las dependencias usan `service_healthy` o
`service_completed_successfully`.

## Que viaja y como

| Origen | Contenido |
|---|---|
| git | Config determinista de dev (`backend/<svc>/.env.dev`, `frontend/.env.development`), el realm de Keycloak, las policies de MinIO, los scripts de init |
| `.env.local` (gitignoreado) | Siete valores: 4 de Cloudflare R2 + Mapbox, Brevo y Google Maps |
| R2 `runtime/` (~85 MB) | El `.pbf` de Bogota, los dumps de seed y el modelo AVM con su registro |
| R2 `datasets/` (~480 MB) | Scrape y CSVs de entrenamiento. Opcional, `make data-pull` |

Las rutas dentro de `runtime/` espejan las del repo, asi que el pull es un
`mc mirror` directo sin logica de mapeo. Ver
[[adr-dev-config-versioned-artifacts-in-r2]] para el porque de cada corte.

Los grafos de ORS **no** viajan: se reconstruyen desde el `.pbf` en ~145 s, y ORS
detecta un `.pbf` cambiado comparando su tamano en bytes contra el `stamp.txt` de
cada perfil.

## Los one-shots

Todos idempotentes, todos con centinela. Ver
[[adr-infra-reconciled-by-init-jobs]] para el patron.

- **`minio-init`** — crea los 4 buckets, registra las 3 policies de
  [infra/minio/policies/](infra/minio/policies) y da de alta un **usuario** por
  servicio con su policy adjunta.
- **`keycloak-init`** — fija los client secrets de `users-ms-admin` y
  `users-ms-auth`, que el export del realm enmascara como `**********`.
- **`seed-db`** — restaura los 4 dumps saltando las tablas que ya tienen filas.
  Espera a que los servicios esten healthy porque los dumps son `--data-only`.
- **`seed-dev-user`** — crea `dev@example.com` llamando a `POST /v1/auth/register`
  y le asigna el rol `admin`. No hace INSERT: `accounts.account_id` tiene que ser
  el `sub` que asigna Keycloak, y ese invariante vive en `RegisterAccountUseCase`.
  Por eso `keycloak-init` **no** puede pre-crear ese usuario.
- **`mlflow-init`** — copia el registro al volumen y espeja los artifacts a
  `s3://mlflow-artifacts/`, antes de que arranque el server porque el backend
  store es sqlite.

## Guardas del Makefile

`bootstrap` depende de `check-env` y `up` de `check-artifacts`. Fallan temprano y
con el comando de arreglo, porque el modo de falla alternativo es peor: ORS
levantando a medias o `seed-db` sin encontrar los dumps, varios minutos despues.

`mc` corre en contenedor con `--user $(id -u)`, asi que el host no instala nada y
los archivos bajados no quedan con owner root.

## Claims

- `make bootstrap` exige `.env.local` con las 4 claves de R2 y aborta con el comando de arreglo si falta ([Makefile](Makefile)).
- `make up` aborta si falta el `.pbf`, los dumps de seed o el registro de MLflow ([Makefile](Makefile)).
- El compose define 24 services, de los cuales 6 son one-shots y 14 declaran healthcheck ([docker-compose.yml](docker-compose.yml)).
- El entrypoint de los cuatro MS corre `alembic upgrade head` antes de uvicorn ([service-entrypoint.sh](infra/dev/service-entrypoint.sh)).
- `develop` no publica puertos; los publican los servicios de aplicacion ([docker-compose.yml](docker-compose.yml)).
- Los grafos de ORS se reconstruyen desde el `.pbf` y cada perfil guarda en `stamp.txt` el tamano en bytes del `.pbf` con el que se construyo.
- `seed-dev-user` crea el usuario por `POST /v1/auth/register`, no por INSERT ([seed-dev-user.py](infra/dev/seed-dev-user.py)).
