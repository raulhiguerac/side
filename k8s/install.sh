#!/usr/bin/env bash
#
# install.sh — orquestador del bootstrap de Side (kind + Cilium + microservicios).
#
# NO tiene lógica de fases: solo decide QUÉ correr y en qué ORDEN. Cada fase vive
# en scripts/NN-*.sh (single responsibility, invocable suelto y por un futuro Makefile).
#
# Uso:
#   ./install.sh                 # corre todas las fases en orden
#   ./install.sh cluster         # corre solo una fase
#
set -euo pipefail
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts"

# Mapa fase -> script (el nombre de fase es lo que teclea el usuario / el Makefile).
declare -A STEPS=(
  [cluster]="01-cluster.sh"
  [plataforma]="02-plataforma.sh"
  [microservicios]="03-microservicios.sh"
  [exposicion]="05-exposicion.sh"
  [policies]="06-policies.sh"
)
# Orden de ejecución para 'all' (los mapas de bash no preservan orden).
ORDER=(cluster plataforma microservicios exposicion policies)

run() { bash "$SCRIPTS_DIR/${STEPS[$1]}"; }

main() {
  local target="${1:-all}"
  if [[ "$target" == "all" ]]; then
    for step in "${ORDER[@]}"; do run "$step"; done
  elif [[ -n "${STEPS[$target]:-}" ]]; then
    run "$target"
  else
    echo "fase desconocida: '$target'"
    echo "fases: ${ORDER[*]} | all"
    exit 1
  fi
}

main "$@"