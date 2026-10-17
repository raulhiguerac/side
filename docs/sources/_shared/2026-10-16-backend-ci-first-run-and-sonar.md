---
title: Primera ejecución del CI de backend (#34), SonarQube Cloud free y estado del ruleset de main
captured-from: conversation
captured-on: 2026-10-16
participants: [author, claude]
---

## Context
El PR #34 (CI de backend, ruff en verde y deps de test) fue la primera ejecución real de `backend-ci.yml`. Se mergeó, y el autor activó SonarQube Cloud en plan free.

## Key conclusions
- En el PR #34, `changes` detectó los 4 servicios (tocaba `backend/ruff.toml` y los workflows). Los 8 jobs `lint`/`test` y `ci-ok` pasaron, cada uno en unos 30 s.
- El PR #34 se mergeó el 2026-10-16 (2026-10-17 UTC) con bypass de admin, sin aprobación y con merge commit, aunque el ruleset de `main` pide 1 aprobación e historial lineal.
- El ruleset de `main` exige 1 review, historial lineal y bloquea borrado y force-push. El rol admin tiene bypass `always`. Todavía no exige status checks, así que `ci-ok` no bloquea nada.
- El modo automático de Claude Code bloquea `gh pr merge --admin` ("Merge Without Review"): los merges con bypass los hace el autor.
- SonarQube Cloud está en análisis automático (no hay `sonar-project.properties` en el repo), así que no ve cobertura. Su check se llama "SonarCloud Code Analysis" y no es obligatorio.
- Sonar marcó 3 avisos en `_backend-lint-unit-tests.yml`. Hoy queda 1:
  - `uv run` sin `--locked` ni `--no-build` (2 avisos): resuelto con `uv run --no-sync --no-build pytest tests/unit`. Su regla es estática y no reconoce que `--no-sync` ya evita compilar.
  - `uv sync --locked` sin `--no-build` (1 aviso): sigue abierto y deja el Quality Gate en "C Security Rating". `brevo-python==1.2.0` solo publica sdist y uv no permite excepciones por paquete. Con uv 0.13 los otros 3 servicios instalan bien con `--no-build`.
- Un job `changes` se quedó en `in_progress` aunque todos sus pasos y el run entero habían terminado en éxito. Fue un fallo de estado de GitHub y se resolvió con `gh run rerun`.

## Open questions
- Si conviene mantener `required_linear_history` cuando los merges con bypass entran como merge commit.

## Next steps
- Exigir `ci-ok` en el ruleset de `main` (regla "Require status checks to pass").
- Dependabot para el ecosistema `github-actions`, porque las actions están fijadas por SHA.
- CI del front con el mismo patrón (`lint:check`, `typecheck`, build).
- Fijar `uvx ruff@0.17.1` en el hook post-edit y en `scripts/audit.sh`.
- Cobertura en Sonar: `coverage.xml` desde el CI y escáner en el workflow, en vez del análisis automático.
- Sustituir brevo-python y añadir `--no-build` al `uv sync`.
