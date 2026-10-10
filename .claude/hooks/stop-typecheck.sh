#!/usr/bin/env bash
# Stop: si hay .vue/.ts cambiados en frontend/src, corre vue-tsc en el devcontainer; exit 2 impide cerrar el turno.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CACHE="$ROOT/.claude/.cache"
active=$(jq -r '.stop_hook_active // false')
cd "$ROOT" || exit 0

changed=$(git status --porcelain --untracked-files=all -- frontend/src | grep -E '\.(vue|ts)$')
[[ -z "$changed" ]] && exit 0

# Huella del estado actual del front: si no cambió desde el último resultado, no se repite.
state=$({
  git diff HEAD -- frontend/src
  git ls-files -z --others --exclude-standard -- frontend/src | xargs -0 cat 2>/dev/null
} | shasum | cut -d' ' -f1)
mkdir -p "$CACHE"
[[ "$(cat "$CACHE/typecheck-ok" 2>/dev/null)" == "$state" ]] && exit 0
if [[ "$active" == "true" && "$(cat "$CACHE/typecheck-failed" 2>/dev/null)" == "$state" ]]; then
  jq -n '{systemMessage: "vue-tsc sigue fallando con los mismos cambios; se deja terminar el turno para no entrar en bucle."}'
  exit 0
fi

dc() { docker compose -f "$ROOT/docker-compose.yml" "$@"; }
if [[ -z "$(dc ps --status running -q develop 2>/dev/null)" ]]; then
  jq -n '{systemMessage: "Typecheck omitido: el devcontainer develop está apagado."}'
  exit 0
fi

if out=$(dc exec -T develop bash -lc 'cd /workspace/frontend && npm run --silent typecheck' 2>&1); then
  echo "$state" >"$CACHE/typecheck-ok"
  exit 0
fi
echo "$state" >"$CACHE/typecheck-failed"
{
  echo "vue-tsc encontró errores de tipos; corrígelos antes de terminar:"
  grep -E 'error TS' <<<"$out" | head -n 30
} >&2
exit 2
