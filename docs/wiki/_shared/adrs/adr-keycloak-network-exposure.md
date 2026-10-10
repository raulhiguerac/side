---
title: ADR-0010 — Keycloak sin exposición pública; la gestión de roles pasa por users-service
status: stable
last-verified: 2026-09-28
owners: [_shared, users-service]
related:
  - "[[adr-auth-keycloak-jwt]]"
  - "[[adr-cilium-cni-gateway]]"
  - "[[adr-firebase-removal]]"
  - "[[users-service-keycloak]]"
  - "[[frontend-admin-panel]]"
sources: []
decision-date: 2026-09-28
decision-status: accepted
---

# ADR-0010 — Keycloak sin exposición pública; la gestión de roles pasa por users-service

**TL;DR:** en k8s, Keycloak no tiene ruta pública y su namespace es default-deny. Solo entran users-service (todo) y el resto de los microservicios (solo JWKS). El admin del negocio gestiona roles (moderadores, etc.) desde el panel admin vía users-service; la consola de Keycloak es solo para ops, por `port-forward`.

## Contexto

Keycloak es el IdP único ([[adr-auth-keycloak-jwt]]): quien controla su consola o su Admin API controla todas las cuentas. Al llevar el sistema a internet, su namespace es el más sensible del clúster.

Dos hechos acotan qué tan cerrado puede quedar:

- **El navegador hoy no habla con Keycloak.** El login es por password grant: users-service llama al token endpoint con el cliente confidencial `users-ms-auth` y le devuelve una cookie al front ([auth_client.py:45](backend/users-service/src/app/integrations/identity_provider/keycloak/auth_client.py#L45)).
- **No solo users-service lo necesita.** catalog, properties y analytics validan el JWT localmente y bajan las llaves públicas de `KC_JWKS_URL` (`/realms/core/protocol/openid-connect/certs`). Una política que solo deje pasar a users los rompe al rotar llaves o al levantar un pod nuevo.

Además el admin del negocio necesita gestionar moderadores y otros roles, y no es aceptable que eso implique acceso a la consola de Keycloak ni `kubectl exec`.

## Decisión

1. **Sin ruta pública.** No hay `HTTPRoute` hacia Keycloak en el Gateway ([[adr-cilium-cni-gateway]]).
2. **Namespace default-deny, con ingress explícito:**
   - users-service → Keycloak: permitido completo (token endpoint + Admin API).
   - catalog, properties, analytics → Keycloak: solo `GET /realms/core/protocol/openid-connect/certs`, como regla L7 de `CiliumNetworkPolicy`. Una `NetworkPolicy` estándar no filtra por path; Cilium sí.
3. **La gestión de roles es una feature de la app.** El panel admin llama a endpoints admin de users-service (protegidos por el realm role `admin` del JWT), y users-service asigna o quita realm roles vía Admin API con el service account `users-ms-admin`. Las reglas de negocio (p. ej. un admin no se quita el rol a sí mismo) y la auditoría viven en users-service.
4. **La consola es para ops, por `kubectl port-forward`.** Usa el RBAC del clúster y no expone nada. El admin bootstrap del realm `master` queda como break-glass; el uso diario es con un admin nominal con MFA.

**Cuando llegue Google sign-in** ([[adr-firebase-removal]] lo resuelve con Identity Brokering), el navegador sí tiene que llegar a Keycloak por redirect. En ese momento se publica **solo** `/realms/core/*` en un hostname propio, y la consola queda en `KC_HOSTNAME_ADMIN`, sin ruta pública.

## Alternativas consideradas

- **Netpol que solo deje pasar a users-service** — rompe la validación de JWT del resto de los microservicios.
- **Exponer la consola con IP allowlist** — la superficie de login admin queda en internet; un allowlist sobre IP de casa o móvil es frágil.
- **Ingress interno detrás de VPN/Tailscale o Cloudflare Access / oauth2-proxy** — correcto cuando haya más de una persona de ops; para un solo operador, `port-forward` da lo mismo sin infraestructura extra.
- **Que el admin del negocio use la consola de Keycloak** — le da poder sobre todo el realm, sin reglas de negocio ni auditoría propia.

## Consecuencias

- ✅ Keycloak no tiene superficie pública mientras el login sea por password grant.
- ✅ El admin gestiona roles con la UI del producto, sin credenciales de Keycloak.
- ✅ El service account sigue con privilegio mínimo: `view-users` + `manage-users`, sin `realm-admin`.
- ❌ Hay que construir los endpoints de roles en users-service y la vista en el panel admin; hoy no existen.
- ❌ Asignar realm roles puede exigir al service account ver roles del realm (`view-realm` o permisos finos); se valida al implementar.
- ❌ La regla L7 ata la política de red a Cilium; con otro CNI hay que degradar a L4 (puerto de Keycloak).
- ❌ Google sign-in reabre una superficie pública (solo `/realms/core/*`).

## Claims

- El cliente de Admin de Keycloak de users-service crea cuentas, fija passwords y borra cuentas, pero no asigna roles ([admin_client.py](backend/users-service/src/app/integrations/identity_provider/keycloak/admin_client.py)).
- El login de users-service obtiene tokens con email y password contra Keycloak, sin redirect del navegador ([auth_client.py:45](backend/users-service/src/app/integrations/identity_provider/keycloak/auth_client.py#L45)).
- catalog, properties y analytics declaran `KC_JWKS_URL` en su configuración ([catalog settings.py:14](backend/catalog-service/src/app/core/config/settings.py#L14), [properties settings.py:15](backend/properties-service/src/app/core/config/settings.py#L15), [analytics settings.py:8](backend/analytics-service/src/app/core/config/settings.py#L8)).
- El acceso admin se decide por el realm role `admin` en `realm_access.roles` del JWT ([properties auth.py:93](backend/properties-service/src/app/api/deps/auth.py#L93)).
