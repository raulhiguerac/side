---
title: Dev workflow — reglas de trabajo del monorepo
status: stable
last-verified: 2026-10-18
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
  - ../../sources/_shared/2026-10-16-backend-ci-reusable-and-test-deps.md
  - ../../sources/_shared/2026-10-16-backend-ruff-lint-green.md
  - ../../sources/_shared/2026-10-16-backend-ci-caller-and-gitignore.md
  - ../../sources/_shared/2026-10-16-backend-ci-first-run-and-sonar.md
  - ../../sources/users-service/2026-10-18-smtp-email-adapter-and-api-layout.md
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
valores: las cuatro claves de R2 y las de Mapbox, Brevo y Google Maps. La de Brevo ya no la
lee ningún código: el email pasó a SMTP y faltan pasar sus credenciales a
`.env.local.example` ([[users-service-email]]). Los
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
- **Rebase and merge en GitHub**, no squash, para conservar los commits atómicos. Hasta el 2026-10-16 la regla era merge commit, pero el ruleset de `main` exige historial lineal, que solo admite rebase o squash.
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
| CI backend | En cada PR (`opened`, `synchronize`, `reopened`) | `changes` detecta los servicios tocados; por cada uno, el reusable corre `lint` (ruff 0.17.1 sobre todo el servicio) y `test` (Python 3.10, `uv sync --locked`, `pytest tests/unit`); `ci-ok` resume | Cuando la protección de rama exija `ci-ok` (aún no configurada) | `.github/workflows/backend-ci.yml` → `_backend-lint-unit-tests.yml` |
| SonarQube Cloud (plan free) | En cada PR (app de GitHub, análisis automático) | Quality Gate sobre el código nuevo; sin cobertura, porque el análisis automático no la recibe | No: check "SonarCloud Code Analysis" consultivo | Configuración en SonarQube Cloud; no hay `sonar-project.properties` |

Detalles del hook `Stop`:
- Guarda en `.claude/.cache/` (ignorado por git) la huella de los cambios de `frontend/src`; si no cambió desde la última corrida verde, no repite vue-tsc (~6 s).
- Si vuelve a fallar con exactamente los mismos cambios en un turno que ya bloqueó, deja terminar con un aviso: evita un bucle infinito cuando el error no es corregible en ese momento.

Si el devcontainer está apagado, los dos hooks avisan y no bloquean: nunca caen al host.

**Comandos base** (definidos una vez, los usan hooks y `audit.sh`): en `frontend/package.json`, `lint:check` (`eslint --ext .ts,.vue src`; sin `--ext` ESLint no revisa los `.vue`) y `typecheck` (vue-tsc 2 con TypeScript 5.6 fijados vía `npx`, sin tocar las dependencias del proyecto).

**Saltarlo en una emergencia:** `/hooks` en Claude Code para desactivarlos en la sesión, o `"disableAllHooks": true` en `.claude/settings.local.json` (personal, no se commitea).

**CI backend (2026-10-16).** El reusable recibe `path` (un servicio por llamada) y `python-version` (por defecto `3.10`, la de los Dockerfiles). GitHub solo acepta reusables directamente en `.github/workflows/`, sin subcarpetas; el prefijo `_` los distingue de los callers. Las deps de test de los 4 servicios viven en `[dependency-groups] dev`: `uv sync` las instala y el `--no-dev` de los Dockerfiles las deja fuera de la imagen. Los unit tests pasan en entorno limpio y el lint está en verde.

**Config de ruff (2026-10-16).** `ruff==0.17.1` está fijado en el grupo `dev` de cada servicio, así que `uv run ruff check .` coincide con el CI. La config es común en `backend/ruff.toml`: analytics, properties y users la toman por descubrimiento, y catalog la extiende (`extend = "../ruff.toml"`) y conserva su `E712`. Lleva:
- `target-version = "py310"` y `known-first-party = ["app"]`: con la config en `backend/`, ruff ya no lee el `requires-python` de cada servicio y deja de reconocer `app` como código propio;
- `extend-immutable-calls` para `fastapi.Depends`/`Query`, el falso positivo de `B008`;
- `BLE001` y `S110` ignorados por el cache-aside fail-open (ver [[adr-cache-optional-layer]]).

El hook `post-edit-lint.sh` y `scripts/audit.sh` todavía usan `uvx ruff` sin versión.

**Caller `backend-ci.yml` (2026-10-16).** No tiene filtro `paths` en el `on`: arranca en todos los PRs y decide qué correr en tres jobs.
- `changes`: `dorny/paths-filter` (permiso `pull-requests: read`) arma la lista de servicios con cambios bajo `backend/<servicio>/**`. Si cambia algo compartido (`backend/ruff.toml` o cualquiera de los dos workflows), la lista son los 4 servicios.
- `lint_and_test`: matriz sobre esa lista (`fail-fast: false`) que llama al reusable con `path: backend/<servicio>`. Se salta si la lista está vacía.
- `ci-ok`: corre siempre y falla si algún job anterior terminó en `failure` o `cancelled`.

`ci-ok` es el único check que debe ser obligatorio en la protección de rama. Los nombres de la matriz cambian según el PR (`lint_and_test (<servicio>) / lint`), y un filtro `paths` en el `on` dejaría los checks obligatorios esperando para siempre en los PRs que no tocan backend. La `concurrency` agrupa por workflow y número de PR, con `cancel-in-progress`: un push nuevo cancela la ejecución anterior del mismo PR. Corrió por primera vez en el PR #34: detectó los 4 servicios y los 8 jobs y `ci-ok` pasaron, cada uno en unos 30 s. Si GitHub deja un job en `in_progress` con todos sus pasos terminados (pasó una vez con `changes`), se arregla con `gh run rerun <run-id>`.

**Sonar sobre el CI (2026-10-16).** Sonar marcó `uv run` sin `--locked` ni `--no-build`. El paso de tests usa `uv run --no-sync --no-build`: el entorno ya viene de `uv sync --locked`, y `--no-build` se añade solo porque la regla de Sonar es estática. Sigue abierto el aviso de `uv sync` sin `--no-build`, que deja su Quality Gate en "C Security Rating": users necesita compilar `brevo-python` (solo publica sdist) y uv no admite excepciones por paquete. Ver [[open-items]].

**Ruleset de `main` (2026-10-16).** Exige 1 aprobación e historial lineal, y bloquea borrar la rama y el force-push. El rol admin tiene bypass `always`. Todavía no exige status checks. Claude Code no puede mergear con bypass (`gh pr merge --admin` lo bloquea su modo automático por "Merge Without Review"), así que esos merges los hace el autor.

**`.gitignore` (2026-10-16).** El de la raíz cubre las cachés y artefactos de las herramientas (`.venv/`, `.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`, `coverage.xml`, `dist/`, `build/`) y los archivos de editor y sistema (`.idea/`, `.vscode/`, `*.swp`, `.DS_Store`). Los servicios backend ya no tienen `.gitignore` propio; `frontend/` conserva el suyo.

**Pendiente:** exigir `ci-ok` en el ruleset de `main`, Dependabot para las actions fijadas por SHA, cobertura en Sonar, ruff fijado en el hook y en `audit.sh`, CI del front, tests del front (Vitest), lint y typecheck en el pre-commit, y un typechecker para el backend (ningún servicio tiene mypy/pyright). Ver [[open-items]].

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
- `.gitignore` de la raíz ignora `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `htmlcov/` y `.DS_Store`; ningún `backend/*-service` tiene `.gitignore` propio ([.gitignore](.gitignore)).
- `.github/workflows/backend-ci.yml` corre en `pull_request` (`opened`, `synchronize`, `reopened`) sin filtro `paths`, con `concurrency` por número de PR y `cancel-in-progress: true` ([backend-ci.yml](.github/workflows/backend-ci.yml)).
- En `backend-ci.yml`, el job `changes` usa `dorny/paths-filter` con un filtro por servicio más uno `shared` (`backend/ruff.toml` y los dos workflows) que expande la salida `services` a los 4 servicios ([backend-ci.yml](.github/workflows/backend-ci.yml)).
- En `backend-ci.yml`, `lint_and_test` es una matriz sobre `services` que llama a `./.github/workflows/_backend-lint-unit-tests.yml` con `path: backend/<servicio>`, y `ci-ok` corre con `if: always()` y falla si algún job previo terminó en `failure` o `cancelled` ([backend-ci.yml](.github/workflows/backend-ci.yml)).
- `.github/workflows/_backend-lint-unit-tests.yml` es un reusable (`on: workflow_call`) con inputs `path` y `python-version` (por defecto `"3.10"`) y dos jobs: `lint` (ruff-action con `version: "0.17.1"`) y `test` (`uv sync --locked` + `uv run --no-sync --no-build pytest tests/unit`) ([_backend-lint-unit-tests.yml](.github/workflows/_backend-lint-unit-tests.yml)).
- `backend/ruff.toml` fija `target-version = "py310"`, ignora `BLE001` y `S110`, declara `fastapi.Depends`/`fastapi.Query` como llamadas inmutables para `B008` y `app` como first-party; `catalog-service/pyproject.toml` la extiende ([backend/ruff.toml](backend/ruff.toml)).
- Los 4 servicios fijan `ruff==0.17.1` en `[dependency-groups] dev`, la misma versión que usa el job `lint` del reusable ([users-service/pyproject.toml](backend/users-service/pyproject.toml)).
- Los 4 servicios backend declaran sus deps de test en `[dependency-groups] dev`, y sus Dockerfiles instalan con `uv sync --frozen --no-dev` ([users-service/pyproject.toml](backend/users-service/pyproject.toml), [users-service/Dockerfile](backend/users-service/Dockerfile)).
