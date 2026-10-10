---
title: Dev workflow — reglas de trabajo del monorepo
status: stable
last-verified: 2026-10-09
owners: [_shared]
related:
  - "[[architecture]]"
  - "[[glossary]]"
  - "[[local-bootstrap]]"
  - "[[adr-seaweedfs-dev-object-storage]]"
sources:
  - ../../sources/_shared/2026-05-23-repo-tooling-claude-md-precommit.md
  - ../../sources/_shared/2026-10-05-stacked-prs-and-roadmap.md
  - ../../sources/_shared/2026-09-07-entorno-dev-migrable.md
  - ../../sources/_shared/2026-09-27-minio-a-seaweedfs-y-rclone.md
---

## TL;DR

Reglas de trabajo cross-cutting: (1) discutir antes de codificar y (2) auditar al terminar hasta production grade, ambas en `.claude/CLAUDE.md`; (3) un harness de checks automáticos que corre todo en el devcontainer (hooks de Claude Code, `make audit`, pre-commit de wiki staleness).

## Levantar el entorno

Los comandos, los puertos y el detalle de la topologia estan en [[local-bootstrap]]
y en [`README.md`](README.md). Resumido: `make bootstrap && make up`. El unico requisito del host es Docker; los comandos
y los puertos estan en [`README.md`](README.md). Tres cosas que conviene entender
antes de tocar nada:

**Que va a git y que no.** La config determinista de dev —contrasenas de Postgres,
secrets de Keycloak, claves S3— esta versionada a proposito en
`backend/<servicio>/.env.dev`: son valores de `localhost`, y fijarlos es lo que
hace el entorno reproducible. En `.env.local` (gitignoreado) van solo siete
valores: las cuatro claves de R2 y las de Mapbox, Brevo y Google Maps. Los
binarios y los datos no van al repo: los baja `make bootstrap` desde R2.

**Reconciliar, no restaurar.** Cuatro one-shots dejan la infra en su estado
esperado en cada `up`, y todos son idempotentes: `minio-init` (los buckets; los
usuarios S3 se declaran en `infra/seaweedfs/s3.json`), `keycloak-init` (los client secrets, que el
export del realm enmascara), `seed-db` (los dumps, saltando tablas que ya tienen
filas; comentado por ahora junto con las apps) y `mlflow-init` (el registro y los artifacts del AVM). El patron existe
porque `--import-realm` de Keycloak salta si el realm ya existe: lo que tiene que
poder re-aplicarse no puede vivir en un archivo de import.

**Los seeds no borran.** Cada uno chequea una tabla centinela y salta si ya hay
datos. Para empezar de cero esta `make reset`, que pide confirmacion.

**Por ahora las apps corren en el devcontainer.** Los servicios de aplicacion y los
seeds estan comentados en el compose: `make up` levanta solo la infra, y cada
server y el front se arrancan a mano dentro de `develop`. `make seed` no funciona
mientras tanto.

## CLAUDE.md — discuss before code

`.claude/CLAUDE.md` en la raíz del repo se carga automáticamente al inicio de cada sesión de Claude Code. Contiene una regla dura:

**Cero código sin debate previo.** El flujo obligatorio es:
1. Usuario describe el problema.
2. Claude expone su entendimiento + trade-offs.
3. Usuario confirma.
4. Solo entonces se escribe código.

**Terminado significa auditado (regla #2, 2026-10-09).** Al cerrar un trabajo, de Claude o del usuario, se corren los checks de lo tocado (lint, vue-tsc, ruff, pytest, `/wiki-lint`) dentro del devcontainer, se revisa el diff buscando bugs y smells, y se itera hasta production grade o hasta dejar explícito lo que falta. Incluye consultar la wiki antes de afirmar cómo funciona algo, revisar el estado del PR antes de hacer push y reportar las verificaciones con el comando exacto. Ver "Harness" más abajo.

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

## Ramas y PRs (2026-10-05)

`feat/front-admin-panel` llegó a 50 commits por delante de `main`, mezclando backend, panel admin, catálogo y refactors, y no había forma de revisarla como un solo PR. Las reglas que salieron:

- **Una rama por tema, con los refactors aparte de las features.** Una rama de feature no acumula trabajo de otros servicios.
- **Merge commit en GitHub**, no squash, para conservar los commits atómicos.
- **Partir una rama ya hecha:** cherry-pick a **ramas apiladas** que salen de `main`, cada PR con base en la rama anterior. El orden lo fijan las dependencias: en ese caso, build verde del front → backend de properties → panel de properties → catálogo → refactors.
  - Los ingest de docs viajan con la rama donde ya existe el código que describen.
  - **Un commit que mezcla backend y front se parte en dos.** En la rama de backend: `git cherry-pick -n <sha>`, `git rm` de lo del front y `git commit -C <sha>`. En la rama del front: cherry-pick normal, resolviendo con `--ours` los archivos de backend, que ya están.
  - **Prueba de que no se perdió nada:** el `git diff` entre la última rama (más las independientes) y la original tiene que dar vacío.
  - Conviene hacerlo en un `git worktree` aparte, para no tocar los cambios sin commitear. Dentro del devcontainer, git necesita `safe.directory` para ese worktree.
- **Al mergear un PR de la pila, GitHub reapunta solo el siguiente a `main`**, aunque `deleteBranchOnMerge` esté apagado.
- **No mergear un PR contra una base que ya entró a `main`:** sus commits quedan fuera. Pasó con #20, y se resolvió abriendo un PR nuevo de la misma rama contra `main` (#21), sin revertir nada.

## Harness — checks automáticos (2026-10-09)

Un **harness** es el conjunto de controles que rodean el trabajo para que un error se detenga solo, sin depender de que alguien se acuerde de correr algo. Se armó después de que dos errores de tipos llegaran a `main` (#22, #23): el build no typecheckea los `.vue` y nadie corría `vue-tsc`.

**Regla de oro: todo corre dentro del devcontainer.** El host queda limpio (sin Python, uv ni ruff); los hooks solo orquestan desde el host con `jq`, `git` y `docker compose exec -T develop`.

| Puesto | Cuándo | Qué corre | Bloquea | Dónde vive |
|---|---|---|---|---|
| Hook `PostToolUse` | Cada vez que Claude edita un archivo | `.vue`/`.ts` de `frontend/src` → `eslint --fix` del archivo; `.py` de `backend/*-service` → `uvx ruff check` del archivo, desde la carpeta del servicio | Sí: exit 2 devuelve los errores a Claude | `.claude/hooks/post-edit-lint.sh` |
| Hook `Stop` | Cuando Claude termina el turno, si hay `.vue`/`.ts` cambiados | `npm run typecheck` (vue-tsc) | Sí: no deja cerrar el turno con errores de tipos | `.claude/hooks/stop-typecheck.sh` |
| `make audit` | A mano | ruff + pytest por servicio, eslint, vue-tsc, links de la wiki → `audit-report.txt` | No (es un reporte) | `scripts/audit.sh` |
| Pre-commit | En cada commit (desde el devcontainer) | Wiki staleness | No (solo avisa) | `.pre-commit-config.yaml` |

Detalles del hook `Stop`:
- Guarda en `.claude/.cache/` (ignorado por git) la huella de los cambios de `frontend/src`; si no cambió desde la última corrida verde, no repite vue-tsc (~6 s).
- Si vuelve a fallar con exactamente los mismos cambios en un turno que ya bloqueó, deja terminar con un aviso: evita un bucle infinito cuando el error no es corregible en ese momento.

Si el devcontainer está apagado, los dos hooks avisan y no bloquean: nunca caen al host.

**Comandos base** (definidos una vez, los usan hooks y `audit.sh`): en `frontend/package.json`, `lint:check` (`eslint --ext .ts,.vue src`; sin `--ext` ESLint no revisa los `.vue`) y `typecheck` (vue-tsc 2 con TypeScript 5.6 fijados vía `npx`, sin tocar las dependencias del proyecto).

**Saltarlo en una emergencia:** `/hooks` en Claude Code para desactivarlos en la sesión, o `"disableAllHooks": true` en `.claude/settings.local.json` (personal, no se commitea).

**Pendiente:** CI en GitHub (`.github/workflows`), tests del front (Vitest), lint y typecheck en el pre-commit, y un typechecker para el backend (ningún servicio tiene mypy/pyright). Ver [[open-items]].

## Claims

- `make bootstrap` baja de R2 los artefactos que no viven en git (~85 MB: el .pbf de Bogota, los dumps de seed y el modelo AVM) y `make up` levanta los 17 servicios activos del compose, que hoy son solo infra ([Makefile](Makefile), [docker-compose.yml](docker-compose.yml)).
- Los one-shots activos (`minio-init`, `keycloak-init`, `topic-init`, `mlflow-init`) son idempotentes y corren en cada `up`; ninguno pisa datos existentes. `seed-db` y `seed-dev-user` estan comentados ([docker-compose.yml](docker-compose.yml)).
- `.env.local` lleva solo siete valores; el resto de la config de dev esta versionada en `backend/<servicio>/.env.dev` ([.env.local.example](.env.local.example)).
- `.claude/CLAUDE.md` existe en la raíz del repo y se carga al inicio de cada sesión de Claude Code ([.claude/CLAUDE.md](.claude/CLAUDE.md)).
- `.pre-commit-config.yaml` define un hook local `wiki-staleness-check` con `language: system` y `exit 0` — nunca bloquea commits ([.pre-commit-config.yaml](.pre-commit-config.yaml)).
- `scripts/wiki-lint-hook.sh` mapea prefijos de path a servicios y chequea `last-verified` en front-matter de páginas wiki ([scripts/wiki-lint-hook.sh](scripts/wiki-lint-hook.sh)).
- El devcontainer corre `uv tool install pre-commit && pre-commit install` en `postCreateCommand` ([.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)).
- Commits desde el host requieren `pipx install pre-commit && pre-commit install` manualmente — el hook no aplica dentro del container.
- `.claude/settings.json` registra un hook `PostToolUse` (matcher `Edit|Write|MultiEdit`) que corre `.claude/hooks/post-edit-lint.sh` y un hook `Stop` que corre `.claude/hooks/stop-typecheck.sh` ([.claude/settings.json](.claude/settings.json)).
- Los dos hooks ejecutan las herramientas con `docker compose exec -T develop` y salen con código 0 y un aviso si el contenedor `develop` no está corriendo ([.claude/hooks/](.claude/hooks)).
- `frontend/package.json` define `lint:check` y `typecheck`, y `scripts/audit.sh` los invoca ([frontend/package.json](frontend/package.json), [scripts/audit.sh](scripts/audit.sh)).
- `.claude/.cache/` está en `.gitignore` ([.gitignore](.gitignore)).
