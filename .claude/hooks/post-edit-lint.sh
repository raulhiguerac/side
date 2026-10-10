#!/usr/bin/env bash
# PostToolUse: lintea el archivo recién editado dentro del devcontainer; exit 2 devuelve los errores a Claude.
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
file=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[[ -z "$file" ]] && exit 0
rel="${file#"$ROOT"/}"
[[ "$rel" == "$file" ]] && exit 0 # fuera del repo

case "$rel" in
  frontend/src/*.vue | frontend/src/*.ts)
    printf -v target '%q' "${rel#frontend/}"
    cmd="cd /workspace/frontend && node_modules/.bin/eslint --fix $target"
    ;;
  backend/*-service/*.py)
    svc=$(cut -d/ -f2 <<<"$rel")
    printf -v target '%q' "${rel#backend/"$svc"/}"
    cmd="cd /workspace/backend/$svc && uvx ruff check --output-format concise $target"
    ;;
  *) exit 0 ;;
esac

dc() { docker compose -f "$ROOT/docker-compose.yml" "$@"; }
if [[ -z "$(dc ps --status running -q develop 2>/dev/null)" ]]; then
  jq -n --arg f "$rel" '{systemMessage: ("Lint omitido en \($f): el devcontainer develop está apagado.")}'
  exit 0
fi

out=$(dc exec -T develop bash -lc "$cmd" 2>&1) && exit 0
{
  echo "Lint falló en $rel; corrígelo antes de seguir:"
  tail -n 40 <<<"$out"
} >&2
exit 2
