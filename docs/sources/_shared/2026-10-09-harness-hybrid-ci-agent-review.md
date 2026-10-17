---
title: Harness para un modelo híbrido usuario/agente — CI determinista y revisión con agente en GitHub Actions
captured-from: conversation
captured-on: 2026-10-09
participants: [author, claude]
---

## Context
Tras montar el harness (#25: hooks de Claude Code, regla "terminado = auditado", vue-tsc en 0) se evaluó si cubre igual el trabajo del agente y el del usuario, y cómo meter un agente como paso de CI sabiendo que no es determinista.

## Key conclusions
- El harness actual es asimétrico: lo que edita el agente pasa por eslint/ruff (`PostToolUse`) y vue-tsc (`Stop`); lo que edita el usuario en VS Code no pasa por nada hasta `make audit`, y el pre-commit solo revisa wiki staleness.
- Sin CI ni protección de rama, un PR puede mergearse en rojo sin importar quién escribió el código; es el único control que no depende de quién editó ni de dónde.
- Equivalentes del lado del usuario: pre-commit con lint + typecheck sobre lo staged (≈ hook `Stop`) y extensiones `dbaeumer.vscode-eslint` y `charliermarsh.ruff` en `devcontainer.json` (≈ hook `PostToolUse`); hoy el devcontainer solo trae Volar.
- Un agente puede correr en GitHub Actions: la action oficial `anthropics/claude-code-action` revisa PRs y responde a `@claude`, y lee `.claude/CLAUDE.md`, así que las convenciones y la regla de auditoría aplican también en CI. Alternativas: un script contra la API compatible con OpenAI de OpenRouter, o Copilot code review.
- La action funciona con plan Pro o Max, sin API key: `claude setup-token` genera un token OAuth que va como secret `CLAUDE_CODE_OAUTH_TOKEN` y se pasa con `claude_code_oauth_token` (verificado en `docs/setup.md` de la action). Consume el cupo del plan.
- Diseño acordado: los checks deterministas (lint, vue-tsc, ruff, pytest) son obligatorios y bloquean el merge; el agente es consultivo, comenta pero no es check requerido.
- Para acotar costo y riesgo: el review corre al abrir o pasar a listo el PR, con filtros de rutas; permisos de solo lectura + comentar; sin `pull_request_target` sobre forks; el contenido del PR puede intentar inyectar instrucciones, así que el agente no hace push ni merge por su cuenta.

## Open questions
- Autenticación del review: token OAuth del plan (cupo compartido con el uso interactivo) o API key (cobro por uso).
- Si el review también corre en cada push o solo al abrir/listo.

## Next steps
- Workflow con dos jobs: `checks` (obligatorio, reusa `lint:check`, `typecheck`, ruff, pytest) y `review` (consultivo, `claude-code-action`), más protección de rama sobre `main`.
- Pre-commit con lint + typecheck de lo staged, corriendo en el devcontainer.
- Extensiones de ESLint y Ruff en `devcontainer.json`.
- Vitest como siguiente capa (los mismos jobs lo incorporan cuando exista).
