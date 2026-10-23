#!/usr/bin/env bash
# PreToolUse: bloquea `gh pr create` hasta que /structural-review haya corrido sobre el HEAD actual.
set -uo pipefail

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
[[ "$cmd" =~ (^|[\;\&\|]|\$\()[[:space:]]*gh[[:space:]]+pr[[:space:]]+create ]] || exit 0

cwd=$(jq -r '.cwd // empty' <<<"$input")
cwd="${cwd:-${CLAUDE_PROJECT_DIR:-.}}"
head=$(git -C "$cwd" rev-parse HEAD 2>/dev/null) || exit 0
marker=$(git -C "$cwd" rev-parse --path-format=absolute --git-path structural-review-ok)

[[ -f "$marker" && "$(cat "$marker")" == "$head" ]] && exit 0

echo "Antes de abrir el PR corre /structural-review sobre HEAD ($head); al terminar marca el commit como revisado (paso 6 de la skill)." >&2
exit 2
