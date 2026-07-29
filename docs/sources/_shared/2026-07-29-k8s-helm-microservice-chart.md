---
title: K8s self-host infra track — generic Helm microservice chart
captured-from: conversation
captured-on: 2026-07-29
participants: [author, claude]
---

## Context
Started a parallel Kubernetes infra track (learning mode) because the property lifecycle and admin work are blocked. The goal is a self-hosted staging/learning environment, NOT the August beta infra. Work is "on paper" only: the current PC cannot run kind or helm, so authoring is done but nothing is deployed or verified yet.

## Key conclusions

### Scope & strategy
- **Objective:** staging/learning, no beta deadline pressure. Self-host all stateful pieces (Postgres, Redis, MinIO, Kafka) as pods — not managed GCP.
- **Tooling pivot Kustomize → Helm.** Initial manifests were hand-written in Kustomize (to learn raw resources), then converted to a generic Helm chart `k8s/charts/microservice/` reusable for the 4 near-identical microservices via per-service values. Kustomize removed. Rationale: N near-identical services is Helm's parametric axis; Kustomize is the "1 app × N environments" axis. They can recombine later (`helmCharts` + `--enable-helm`) only if a patch needs it.
- **Cluster:** kind local planned first (free, same YAML), GKE later. kindnet does NOT enforce NetworkPolicies — a CNI swap (Calico/Cilium) is required before policies do anything.

### Postgres (CloudNativePG)
- One `Cluster` per service (DB-per-service pattern preserves isolation). `instances` = replica pods (HA), not databases. A Cluster can hold multiple DBs but the microservice pattern maps to one Cluster per service.
- catalog and properties use a **PostGIS** image (`imageName`); users/analytics use the standard image.
- cnpg auto-generates a `<cluster>-app` Secret (keys: username, password, host, port, dbname, uri, jdbc-uri, pgpass). The app reads `DATABASE_URL` from its `uri` key — never hand-written. Services `<cluster>-rw` (primary, follows failover), `-ro` (replicas), `-r` (any).
- Schema is owned by **Alembic** (migrations), not by cnpg init SQL — avoid two sources of truth. Use cnpg `postInitSQL`/`postInitApplicationSQLRefs` (ConfigMap) only for extensions needing superuser, never mounted volumes.

### Migration & startup ordering
- Kubernetes has no `depends_on`; it converges via retries/eventual consistency. Ordering is enforced with initContainers, readiness probes, or (with Helm/Argo) hooks/sync-waves.
- Pattern: a separate **Job** runs `alembic upgrade head`; the app Deployment's initContainer **waits for the migration to be applied (schema == head), not just DB reachability** — otherwise the Service routes traffic to un-migrated pods (a real race). The Job's own initContainer just waits for DB (`pg_isready`).
- Verified: Alembic `env.py` imports only `app.models.*` (sqlmodel), which do NOT import `settings`, so the migration Job needs only `DATABASE_URL` — no full config `envFrom`.
- Jobs do NOT re-run on `kubectl apply` once completed — needs delete+recreate, unique name per version, or a Helm `pre-upgrade` hook.

### Labels, secrets, config (Helm patterns)
- Standard `app.kubernetes.io/*` labels via `_helpers.tpl`; each resource adds `app.kubernetes.io/component` (backend/database/migration) inline. **Selector uses only `selectorLabels` (name+instance) — the immutable minimal subset**; full `labels` (incl. version, env, component) go on metadata + pod template only. `env` comes from `.Values.env` (environment axis).
- `checksum/config` annotation on the pod template (sha256 of the rendered configmap) → rolls pods when config changes (k8s does not restart on ConfigMap change). Goes in annotations, not labels (64-char hash > 63-char label limit).
- ConfigMap data and Secrets are generated dynamically with `range` over maps in values (`config`, `secretData`). Nested range needs `$` for root scope (inside range, `.` rebinds to the loop item). `dig` for optional nested values (survives missing parents; `| default` only covers the leaf).
- **Secrets:** base64 ≠ encryption. Never commit real secrets. Dummy secrets are behind a `createDummySecrets` flag; real ones arrive via Sealed Secrets → Vault dev + ESO (security phase). The app chart references secrets by name (`envFrom`), it does not manage the real ones.
- No custom ServiceAccount/RBAC needed — no workload calls the k8s API; every pod already has the `default` SA. Optional hardening: dedicated SA with `automountServiceAccountToken: false` (deferred to security phase). cnpg operator ships its own RBAC.
- Namespaces handled via `--create-namespace` per install, NOT templated into the chart (anti-pattern: Helm could delete the namespace on uninstall). One namespace per domain + `platform`.

### Incidental finding
- **Bug:** users-service reads env var `BREVO_API_KEY` (`brevo/client.py`) but `.env.example` declares `BREVO_SMTP_KEY` — mismatch means email key is `None` with the example as-is.

## Open questions
- Local `main` branch is diverged from `origin/main` (2 unpushed merge commits, 14 behind) — needs cleanup (likely reset to origin/main) but not yet resolved.

## Next steps
- When a machine with kind + helm is available: `helm lint` + `helm template` to verify (confirms editor's `{{ }}` YAML squiggles are false positives), install the CloudNativePG operator, deploy users to kind.
- Create `values/<service>.yaml` per microservice (catalog/properties with PostGIS image).
- Build/install the `platform` layer (redis, minio, kafka, keycloak, mlflow, ORS) + ingress.
- Security phase: NetworkPolicies (requires Calico/Cilium CNI), Sealed Secrets/ESO, SA hardening, HPA, observability.