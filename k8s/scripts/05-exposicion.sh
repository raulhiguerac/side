#!/usr/bin/env bash
#
# 05-exposicion.sh — Fase 5: exposición vía Cilium Gateway API.
# El reverse proxy = Cilium. Enrutado host-based, un HTTPRoute por servicio.
#
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

log "Fase 5 — exposición (Gateway + HTTPRoute)"

# TODO: Gateway compartido + HTTPRoute por servicio (host-based).
# TODO: cuadrar el issuer de Keycloak (KC_HOSTNAME == KC_ISSUER == URL del navegador).
warn "fase exposicion: pendiente"