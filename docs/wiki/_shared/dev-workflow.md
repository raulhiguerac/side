---
title: Dev workflow — reglas de trabajo del monorepo
status: stable
last-verified: 2026-05-23
owners: [_shared]
related: [[architecture]], [[glossary]]
sources:
  - ../../sources/_shared/2026-05-23-repo-tooling-claude-md-precommit.md
---

## TL;DR

Dos reglas de trabajo cross-cutting: (1) discutir antes de codificar (enforced vía `.claude/CLAUDE.md`), (2) pre-commit hook que avisa cuando el wiki está stale respecto a los archivos tocados en el commit.

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

- `.claude/CLAUDE.md` existe en la raíz del repo y se carga al inicio de cada sesión de Claude Code ([.claude/CLAUDE.md](.claude/CLAUDE.md)).
- `.pre-commit-config.yaml` define un hook local `wiki-staleness-check` con `language: system` y `exit 0` — nunca bloquea commits ([.pre-commit-config.yaml](.pre-commit-config.yaml)).
- `scripts/wiki-lint-hook.sh` mapea prefijos de path a servicios y chequea `last-verified` en front-matter de páginas wiki ([scripts/wiki-lint-hook.sh](scripts/wiki-lint-hook.sh)).
- El devcontainer corre `uv tool install pre-commit && pre-commit install` en `postCreateCommand` ([.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)).
- Commits desde el host requieren `pipx install pre-commit && pre-commit install` manualmente — el hook no aplica dentro del container.
