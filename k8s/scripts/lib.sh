#!/usr/bin/env bash
#
# lib.sh — helpers y config compartidos por los scripts de k8s/scripts/.
# Se SOURCEA desde cada script de fase; no se ejecuta directo.
#

# Evita doble-source si dos scripts lo cargan en la misma sesión.
[[ -n "${_SIDE_K8S_LIB:-}" ]] && return 0
_SIDE_K8S_LIB=1

# K8S_DIR = raíz de k8s/ (padre de este scripts/), resuelto por la UBICACIÓN del
# archivo, no por el cwd → funciona igual desde la raíz del repo o desde un Makefile.
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"

# --- Config (overridable por entorno, p.ej. CLUSTER_NAME=foo ./install.sh) ---
CLUSTER_NAME="${CLUSTER_NAME:-side}"
KIND_CONFIG="$K8S_DIR/kind/config.yml"

# Contexto del kubeconfig que crea kind (siempre 'kind-<nombre>'). Lo pinneamos en
# cada helm/kubectl con --kube-context/--context para NO depender del current-context
# (evita instalar por error en otro cluster). Ver helpers 'kc' y 'h' abajo.
KUBE_CONTEXT="kind-${CLUSTER_NAME}"

# --- Helpers ----------------------------------------------------------------
log()  { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }

# Wrappers que inyectan SIEMPRE el contexto → usa 'kc ...' y 'h ...' en las fases
# en vez de kubectl/helm pelados. Imposible aterrizar en el cluster equivocado.
kc() { kubectl --context "$KUBE_CONTEXT" "$@"; }
h()  { helm --kube-context "$KUBE_CONTEXT" "$@"; }