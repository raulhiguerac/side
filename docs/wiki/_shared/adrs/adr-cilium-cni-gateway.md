---
title: ADR-0007 — Cilium como CNI unificado (CNI + NetworkPolicy + Gateway API)
status: stable
last-verified: 2026-07-31
owners: [_shared]
related:
  - "[[deployment-k8s-helm]]"
  - "[[platform-deps-k8s]]"
  - "[[architecture]]"
sources: [../../../sources/_shared/2026-07-31-k8s-selfhost-infra-design.md]
decision-date: 2026-07-31
decision-status: accepted
---

# ADR-0007 — Cilium como CNI unificado (CNI + NetworkPolicy + Gateway API)

## Contexto

El track de despliegue k8s self-host necesita tres piezas de red: un CNI (red de pods), enforcement de NetworkPolicies (aislamiento este-oeste), y un reverse proxy / entrada L7. El kindnet por defecto de kind **no** aplica NetworkPolicies, así que hacían falta piezas extra de todos modos.

En paralelo, el estándar de entrada cambió: **ingress-nginx quedó retirado** (repo archivado en marzo 2026; su sucesor previsto, InGate, nunca maduró y también se retiró). Kubernetes recomienda migrar a **Gateway API**, no a otro controller de Ingress legacy. Montar ingress-nginx en un proyecto nuevo sería construir sobre algo muerto y sin parches de seguridad.

## Decisión

**Cilium** como capa de red única, que cubre las tres piezas con una sola herramienta:

- **CNI** (datapath eBPF), reemplazando kindnet.
- **NetworkPolicies** — las enforce de verdad (kindnet no).
- **Gateway API** (`Gateway` + `HTTPRoute`) embebido en el cilium-operator, como reverse proxy L7. Reemplaza a Ingress; el cruce de namespaces (un microservicio por namespace) se resuelve con `ReferenceGrant`.

Config asociada en kind: `disableDefaultCNI: true` + `kubeProxyMode: "none"` en `k8s/kind/config.yml`, y Cilium instalado con `kubeProxyReplacement=true`, `k8sServiceHost` = IP del contenedor `<cluster>-control-plane` (red docker `kind`), `k8sServicePort=6443`.

## Alternativas consideradas

- **ingress-nginx** — retirado/archivado en 2026, sin futuro. Descartado.
- **Traefik + un CNI aparte (Calico/Cilium)** — Traefik es el atajo de menor fricción y mantenimiento activo, pero deja el CNI y las NetworkPolicies como pieza separada; no unifica.
- **Envoy Gateway / Istio** — potentes pero más pesados para un track de aprendizaje self-host; no aportan el CNI.

## Consecuencias

- ✅ Una sola herramienta cubre CNI + NetworkPolicy + Gateway → colapsa dos fases del roadmap (exposición y policies) en un stack.
- ✅ Es la migración que recomienda el CNCF tras el archivado de ingress-nginx; skill relevante y actual.
- ✅ Abarata la migración kind→k3s: al no depender de kindnet/flannel ni del Traefik embebido de k3s, la capa de red es idéntica en ambos; solo cambian los flags de bootstrap.
- ❌ Es lo más denso de aprender y más piezas en kind (CRDs de Gateway API, `kubeProxyReplacement`, flags de API server).
- ❌ Con cgroup v2 en algunos hosts Cilium pide ajustes extra; en kind moderno suele ir con defaults.

## Claims

- `k8s/kind/config.yml` declara `disableDefaultCNI: true` y `kubeProxyMode: "none"`.
- Cilium se instala en `k8s/scripts/01-cluster.sh` con `kubeProxyReplacement=true`, `k8sServiceHost` derivado por `docker inspect` del contenedor `<cluster>-control-plane` y `k8sServicePort=6443`.
- El reverse proxy usa Gateway API (`Gateway` + `HTTPRoute`), no Ingress.