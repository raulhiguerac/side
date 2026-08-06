#!/usr/bin/env bash
#
# 03-microservicios.sh — Fase 3: un release Helm por microservicio.
# Cada MS en su propio namespace, con su values.
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

log "Fase 3 — microservicios (helm)"

# TODO: por cada ms en users/catalog/properties/analytics:
#   helm upgrade --install <ms> "$K8S_DIR/charts/microservice" \
#     -n <ms>-ms --create-namespace \
#     -f "$K8S_DIR/charts/microservice/values/<ms>.yaml"
warn "fase microservicios: pendiente"