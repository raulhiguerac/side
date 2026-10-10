#!/usr/bin/env bash
# Chequeos deterministas del monorepo; corre dentro del devcontainer (make audit).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="$ROOT/audit-report.txt"
SERVICES=(users catalog properties analytics)

section() { printf '\n## %s\n\n' "$1"; }

wiki_links() {
  local slugs
  slugs="$(find "$ROOT/docs/wiki" -name '*.md' -exec basename {} .md \; | sort -u)"
  find "$ROOT/docs/wiki" -name '*.md' -not -path '*/_templates/*' | sort | while read -r page; do
    grep -oE '\]\((backend|frontend|infra|docs)/[^)#]+' "$page" | sed 's/^](//' | sort -u | while read -r path; do
      [[ -e "$ROOT/$path" ]] || echo "link roto: ${page#"$ROOT"/} → $path"
    done
    grep -oE '\[\[[a-z][a-z0-9-]*' "$page" | sed 's/^\[\[//' | sort -u | while read -r slug; do
      grep -qxF -- "$slug" <<<"$slugs" || echo "slug inexistente: ${page#"$ROOT"/} → [[$slug]]"
    done
  done
}

{
  echo "# audit $(date -Iseconds)"
  for name in "${SERVICES[@]}"; do
    dir="$ROOT/backend/$name-service"
    export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/$name"
    section "$name-service: ruff"
    (cd "$dir" && uvx ruff check src tests --statistics 2>&1 | head -n 25)
    section "$name-service: pytest (unit)"
    (cd "$dir" && uv sync --frozen -q && uv run --no-sync pytest -q tests/unit -p no:cacheprovider 2>&1 | tail -n 60)
  done
  section "frontend: eslint"
  (cd "$ROOT/frontend" && npm run --silent lint:check 2>&1 | tail -n 80)
  section "frontend: vue-tsc"
  (cd "$ROOT/frontend" && npm run --silent typecheck 2>&1 | tail -n 40)
  section "wiki: links y slugs"
  wiki_links
} > "$REPORT"

echo "audit: $REPORT"
