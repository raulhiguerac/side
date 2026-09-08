---
title: ADR-0007 — Config de dev versionada, secretos en .env.local, artefactos en R2
status: stable
last-verified: 2026-09-07
owners: [_shared]
related:
  - "[[local-bootstrap]]"
  - "[[dev-workflow]]"
  - "[[architecture]]"
  - "[[adr-infra-reconciled-by-init-jobs]]"
sources:
  - ../../../sources/_shared/2026-09-07-entorno-dev-migrable.md
---

## TL;DR

La config de dev se parte en tres por criterio de reproducibilidad, no de
secretismo: lo determinista va al repo, lo que solo un humano puede aportar va a
`.env.local`, y los binarios y datos van a un bucket privado de Cloudflare R2.

## Contexto

Hasta el 2026-09-07 el repo no se podia levantar en otra maquina. El `.env` raiz
era la unica fuente de config y estaba gitignoreado, asi que el arranque dependia
de que alguien lo pasara por fuera del repo. Los cinco `.env.example` que
supuestamente lo documentaban declaraban variables que el codigo no lee y omitian
las que si.

En paralelo, ~565 MB de binarios y datos (extracto OSM, dumps, modelo AVM,
scrape) vivian solo en la maquina de desarrollo.

## Decision

### Tres categorias, y cada cosa cae en una sola

| Categoria | Donde vive | Ejemplos |
|---|---|---|
| Config determinista de dev | git, en `backend/<svc>/.env.dev` | Contrasenas de Postgres, secrets de clientes Keycloak, claves de MinIO, hostnames, TTLs |
| Secretos que solo un humano aporta | `.env.local`, gitignoreado | Las 4 claves de R2 + Mapbox, Brevo, Google Maps |
| Binarios y datos | Cloudflare R2, bajados por `make bootstrap` | `.pbf`, dumps de seed, modelo AVM |

El corte no es "secreto vs publico" sino **reproducible vs no reproducible**. Una
contrasena de Postgres que solo escucha en `localhost` es config, no secreto:
fijarla en el repo es exactamente lo que hace el entorno reproducible. Un
`.env.example` con huecos obliga a cada dev a inventar valores y garantiza drift.

Los siete valores de `.env.local` son irreducibles por un huevo y la gallina: la
credencial que baja los artefactos no puede vivir dentro de los artefactos.

### R2 y no Git LFS

R2 se eligio sobre las alternativas por:

- **S3 API con credenciales estaticas**, scripteable sin interaccion humana. Eso
  descarta Google Drive, que necesita un flujo OAuth por maquina.
- **`mc` ya esta en el stack** por MinIO, asi que el pull reusa el mismo cliente
  y el mismo patron que `minio-init`. Cero herramientas nuevas.
- **Egress gratis**, a diferencia de S3 de AWS.
- **Sin prerequisitos en el host**: `mc` corre en contenedor, mientras que Git LFS
  obliga a un `git lfs install` por maquina y consume cuota de GitHub.

Se descartaron ademas GitHub Releases (assets subidos y versionados a mano) y
Hugging Face (segundo repo que mantener sincronizado).

### Dos prefijos en el bucket

`runtime/` (~85 MB) es obligatorio para arrancar; `datasets/` (~480 MB) solo hace
falta para reentrenar el AVM. Las rutas dentro de `runtime/` espejan las del repo,
asi que el pull es un `mc mirror` directo.

## Consecuencias

- Un clone recibe los directorios de artefactos vacios, con `.gitkeep`. El
  Makefile falla con el comando de arreglo antes de que Docker los monte.
- Abrir el repo al publico no expone datos: todo lo sensible —el modelo y las
  properties scrapeadas— esta detras de la credencial de R2. La unica precaucion
  que queda es que la API key de Google Maps nunca entre al repo.
- Los dumps de seed se generan a mano con `pg_dump --data-only` y hay que
  regenerarlos cuando una migracion toque esas tablas. No hay automatismo.

## Claims

- La config determinista de dev esta versionada en `backend/<svc>/.env.dev` y `frontend/.env.development`; ninguno de los dos esta gitignoreado ([.gitignore](.gitignore)).
- `.env.local` declara siete valores y esta gitignoreado ([.env.local.example](.env.local.example)).
- Los directorios de artefactos (`infra/ors/files`, `infra/seeds`, `infra/mlflow/*`) estan gitignoreados con un `.gitkeep` versionado para que existan tras el clone ([.gitignore](.gitignore)).
- `make bootstrap` y `make data-pull` bajan los dos prefijos con `mc` en contenedor, sin instalar nada en el host ([Makefile](Makefile)).
- Los cinco `.env.example` se eliminaron el 2026-09-07; su contenido salio de cruzar cada `os.getenv` y campo de `BaseSettings` contra el codigo.
