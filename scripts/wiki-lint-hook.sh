#!/usr/bin/env bash
# Wiki staleness check — pre-commit hook
# Warns (never blocks) when staged files touch a service whose wiki pages
# haven't been verified in the last 30 days.

WIKI_DIR="docs/wiki"
THRESHOLD_DAYS=30
TODAY=$(date +%s)
WARNED=0

# Map staged file prefixes to wiki service directories
declare -A SERVICE_MAP=(
  ["backend/analytics-service"]="analytics-service"
  ["backend/catalog-service"]="catalog-service"
  ["backend/properties-service"]="properties-service"
  ["backend/users-service"]="users-service"
  ["frontend"]="frontend"
)

# Get services touched by staged files
touched_services=()
while IFS= read -r file; do
  for prefix in "${!SERVICE_MAP[@]}"; do
    if [[ "$file" == "$prefix"* ]]; then
      service="${SERVICE_MAP[$prefix]}"
      # Add only if not already in the list
      if [[ ! " ${touched_services[*]} " =~ " ${service} " ]]; then
        touched_services+=("$service")
      fi
    fi
  done
done < <(git diff --cached --name-only)

if [ ${#touched_services[@]} -eq 0 ]; then
  exit 0
fi

# Check wiki pages for each touched service
for service in "${touched_services[@]}"; do
  service_wiki="$WIKI_DIR/$service"
  [ -d "$service_wiki" ] || continue

  while IFS= read -r page; do
    last_verified=$(grep "^last-verified:" "$page" 2>/dev/null | head -1 | awk '{print $2}')
    [ -z "$last_verified" ] && continue
    [[ "$last_verified" == "YYYY-MM-DD" ]] && continue

    page_ts=$(date -d "$last_verified" +%s 2>/dev/null) || continue
    days_old=$(( (TODAY - page_ts) / 86400 ))

    if [ "$days_old" -gt "$THRESHOLD_DAYS" ]; then
      if [ "$WARNED" -eq 0 ]; then
        echo ""
        echo "⚠  Wiki staleness warning — pages not verified in ${THRESHOLD_DAYS}+ days:"
        WARNED=1
      fi
      rel_path="${page#./}"
      echo "   ${days_old}d  $rel_path"
    fi
  done < <(find "$service_wiki" -name "*.md" | grep -v _templates)
done

if [ "$WARNED" -eq 1 ]; then
  echo ""
  echo "   Run /wiki-lint in Claude Code to review and update."
  echo ""
fi

exit 0
