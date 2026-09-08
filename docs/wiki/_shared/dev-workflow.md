---
title: Dev workflow — reglas de trabajo del monorepo
status: stable
last-verified: 2026-09-07
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[glossary]]"
  - "[[local-bootstrap]]"
sources:
  - ../../sources/_shared/2026-05-23-repo-tooling-claude-md-precommit.md
  - ../../sources/_shared/2026-09-07-entorno-dev-migrable.md
---

## TL;DR

Dos reglas de trabajo cross-cutting: (1) discutir antes de codificar (enforced vía `.claude/CLAUDE.md`), (2) pre-commit hook que avisa cuando el wiki está stale respecto a los archivos tocados en el commit.

## Levantar el entorno

Los comandos, los puertos y el detalle de la topologia estan en [[local-bootstrap]]
y en [`README.md`](README.md). Resumido: `make bootstrap && make up`. El unico requisito del host es Docker; los comandos
y los puertos estan en [`README.md`](README.md). Tres cosas que conviene entender
antes de tocar nada:

**Que va a git y que no.** La config determinista de dev —contrasenas de Postgres,
secrets de Keycloak, claves de MinIO— esta versionada a proposito en
`backend/<servicio>/.env.dev`: son valores de `localhost`, y fijarlos es lo que
hace el entorno reproducible. En `.env.local` (gitignoreado) van solo siete
valores: las cuatro claves de R2 y las de Mapbox, Brevo y Google Maps. Los
binarios y los datos no van al repo: los baja `make bootstrap` desde R2.

**Reconciliar, no restaurar.** Cuatro one-shots dejan la infra en su estado
esperado en cada `up`, y todos son idempotentes: `minio-init` (buckets, policies
y un usuario con scope por servicio), `keycloak-init` (los client secrets, que el
export del realm enmascara), `seed-db` (los dumps, saltando tablas que ya tienen
filas) y `mlflow-init` (el registro y los artifacts del AVM). El patron existe
porque `--import-realm` de Keycloak salta si el realm ya existe: lo que tiene que
poder re-aplicarse no puede vivir en un archivo de import.

**Los seeds no borran.** Cada uno chequea una tabla centinela y salta si ya hay
datos. Para empezar de cero esta `make reset`, que pide confirmacion.

## CLAUDE.md — discuss before code

`.claude/CLAUDE.md` en la raíz del repo se carga automáticamente al inicio de cada sesión de Claude Code. Contiene una regla dura:

**Cero código sin debate previo.** El flujo obligatorio es:
1. Usuario describe el problema.
2. Claude expone su entendimiento + trade-offs.
3. Usuario confirma.
4. Solo entonces se escribe código.

El archivo está en inglés — mejor adherencia del modelo que en español.

## Pre-commit hook — wiki staleness

### Archivos

| Archivo | Descripción |
|---|---|
| `.pre-commit-config.yaml` | Config versionada — define el hook local |
| `scripts/wiki-lint-hook.sh` | Script del hook |

### Comportamiento

Al hacer commit, el hook:
1. Lee los archivos staged vía `git diff --cached --name-only`.
2. Los mapea a servicios (`backend/analytics-service/` → `analytics-service`, etc.).
3. Busca páginas wiki bajo `docs/wiki/<service>/`.
4. Advierte (nunca bloquea, exit 0) si alguna página tiene `last-verified` > 30 días.

### Instalación (una vez por máquina)

```bash
pipx install pre-commit   # instala el binario globalmente
pre-commit install        # registra el hook en .git/hooks/ del repo
```

El devcontainer lo hace automático vía `postCreateCommand`. En el host hay que correrlo manualmente.

**Nota:** `.git/hooks/` no se versiona — cada dev debe correr `pre-commit install` una vez. `.pre-commit-config.yaml` sí está versionado y define qué hook ejecutar.

### Por qué pipx y no pip

`pipx` instala herramientas CLI en virtualenvs aislados con el binario disponible en PATH. Evita conflictos con el Python del sistema (que en Debian/Ubuntu está marcado como "externally managed").

## Claims

- `make bootstrap` baja de R2 los artefactos que no viven en git (~85 MB: el .pbf de Bogota, los dumps de seed y el modelo AVM) y `make up` levanta los 21 servicios del compose ([Makefile](Makefile), [README.md](README.md)).
- Los cuatro one-shots de infra (`minio-init`, `keycloak-init`, `seed-db`, `mlflow-init`) son idempotentes y corren en cada `up`; ninguno pisa datos existentes ([docker-compose.yml](docker-compose.yml)).
- `.env.local` lleva solo siete valores; el resto de la config de dev esta versionada en `backend/<servicio>/.env.dev` ([.env.local.example](.env.local.example)).
- `.claude/CLAUDE.md` existe en la raíz del repo y se carga al inicio de cada sesión de Claude Code ([.claude/CLAUDE.md](.claude/CLAUDE.md)).
- `.pre-commit-config.yaml` define un hook local `wiki-staleness-check` con `language: system` y `exit 0` — nunca bloquea commits ([.pre-commit-config.yaml](.pre-commit-config.yaml)).
- `scripts/wiki-lint-hook.sh` mapea prefijos de path a servicios y chequea `last-verified` en front-matter de páginas wiki ([scripts/wiki-lint-hook.sh](scripts/wiki-lint-hook.sh)).
- El devcontainer corre `uv tool install pre-commit && pre-commit install` en `postCreateCommand` ([.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)).
- Commits desde el host requieren `pipx install pre-commit && pre-commit install` manualmente — el hook no aplica dentro del container.
