---
title: Reset de password cableado en el front, piezas de auth compartidas y SMTP de users en .env.local
captured-from: conversation
captured-on: 2026-10-24
participants: [author, claude]
---

## Context
Se revisó qué endpoints del back no consume el front y se cerró el primero de la lista: confirmar el reset de password. De paso se movió la config SMTP de users a un `.env.local` por servicio para poder probar el flujo de punta a punta.

## Key conclusions
- **Endpoints sin cablear en el front (2026-10-24):** `POST /v1/users/reactivation/{request,confirm}` y `POST /v1/admin/properties/{id}/estimated-price`; este último sigue bloqueado porque ningún schema devuelve el precio estimado. No se cablean: `POST /v1/users/resolve` y `POST /v1/geo-resolution/by-coordinates/bulk` (los llama properties-service), `GET /v1/geo-resolution/resolve-neighborhood` (a deprecar), `GET /v1/localities/{by-admin-division,by-id}` (sin consumidor) y los `/v1/health`.
- `deleteAccount()` en `api/users.ts` apunta a `DELETE /v1/users/me`, que no existe en el back; su UI está comentada en `SettingsAccount.vue`.
- La vista que pide el correo se renombró a `ForgotPasswordView` (`/forgot-password`); `ResetPasswordView` es la nueva, en `/reset-password`, sin `isLogged`: con ese flag el guard manda a home a un usuario logueado y el token se pierde.
- Piezas compartidas nuevas: `components/shared/AuthLayout.vue` (dos paneles, slot `#aside` a la izquierda y slot por defecto a la derecha), `components/shared/form/NewPasswordFields.vue` (`v-model:password` y `v-model:confirmation`, con el aviso de no coincidencia) y `utils/password.ts` (`MIN_PASSWORD_LENGTH`, `isNewPasswordValid`). `SettingsSecurity` ya los usa; Login y Register todavía no usan `AuthLayout`.
- `useForgotPassword` no muestra el `message` del back (viene en inglés y en 5xx puede filtrar infra): 422 → "Revisa el correo", el resto → mensaje genérico. Tras enviar muestra el aviso y "Ya puedes cerrar esta pestaña o ir a iniciar sesión", porque el flujo sigue en la pestaña nueva que abre el link del correo.
- `useResetPassword` lee `route.query.token` validando con `typeof === "string"` (puede llegar como array) y lo quita con `router.replace({ query: {} })`. La vista no se vuelve a montar al cambiar solo el query, así que el token sigue en memoria; recargar la página lo pierde y se muestra el estado de enlace inválido.
- Estados del confirm: sin token o 401 → `invalidLink` con link a `/forgot-password`; 400 → contraseñas no coinciden; éxito → aviso en la misma vista con link a login, porque el confirm no setea cookies.
- `confirmPasswordReset` manda el token como `Authorization: Bearer` solo en esa request, y el confirm entró en `AUTH_ENTRYPOINTS`: si no, el interceptor trata el 401 como sesión vencida, intenta un refresh y la vista no ve el error.
- users-service: `SMTP_HOST`, `SMTP_FROM`, `SMTP_USERNAME` y `SMTP_PASSWORD` van en `backend/users-service/.env.local`; `.env.dev` deja solo `SMTP_PORT=587`. El patrón `.env.local` del `.gitignore` ya lo ignora en cualquier carpeta.
- `up_dev_env.sh` carga el `.env.local` de cada servicio, si existe, en el subshell que lo lanza: pisa a los `.env.dev` y no llega a la terminal del usuario (a propósito).
- `FRONT_BASE_URL` de dev es `http://localhost:8080`. Al cambiar un `.env.dev` hay que recrear el contenedor `develop` (`docker compose up -d develop`); reiniciar los servicios no alcanza.
- `SMTP_FROM` sigue obligatorio: el `From` lo arma el cliente, y en los proveedores transaccionales el usuario SMTP no es un correo.
- Verificado de punta a punta el 2026-10-24 en `logs/users.log`: request 202 y confirm 200 desde el navegador.

## Open questions
- Qué va en el panel izquierdo de `ResetPasswordView` (hoy vacío).
- `FRONT_BASE_URL` de producción (`https://app.<dominio>`).

## Next steps
- Bug: el cambio de password en Ajustes no funciona: el front manda `current_password` y `ChangePassword` espera `old_password` con `extra="forbid"`, así que siempre da 422. Además, el back borra las cookies tras el cambio y el front muestra éxito como si la sesión siguiera.
- Bug de back: `reset_password_mailer.py:22` calcula `ttl_minutes` con `CACHE_REACTIVATION_TTL_SECONDS` en vez del TTL del reset.
- Reactivación con el mismo patrón: `AuthLayout`, un composable que lea el token y un link desde login.
- Pasar Login y Register a `AuthLayout`.
- Agregar un `.env.local.example` en users-service.
