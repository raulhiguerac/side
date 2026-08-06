#!/usr/bin/env bash
#
# 06-policies.sh — Fase 6: NetworkPolicies (ya con Cilium como CNI, sin recrear cluster).
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

log "Fase 6 — NetworkPolicies"

# TODO: default-deny ingress por namespace + allow explícito de los DNS cruzados
#       (properties-ms → catalog-ms, users-ms, platform).
warn "fase policies: pendiente"