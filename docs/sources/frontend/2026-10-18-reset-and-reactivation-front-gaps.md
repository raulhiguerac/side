---
title: Qué le falta al front (y a la config) para cerrar reset de password y reactivación de cuenta
captured-from: conversation
captured-on: 2026-10-18
participants: [author, claude]
---

## Context
Con el envío ya por SMTP y las `SMTP_*` declaradas en `.env.dev`, se revisó qué falta para que reset y reactivación funcionen de punta a punta, además de las vistas.

## Key conclusions
- **`.env.dev` de users declara las `SMTP_*`.** `SMTP_PORT=587`, `SMTP_HOST` y `SMTP_FROM` vacíos (sin proveedor elegido y sin inventar un dominio para el remitente), y usuario y password van en `.env.local`. Con eso, `get_email_sender()` lanza `SmtpMisconfiguredError` hasta que se llenen.
- **Dos bloqueos fuera del front:**
  - `FRONT_BASE_URL=app.micasaenminutos` en `backend/users-service/.env.dev` no tiene esquema ni TLD, así que el link del correo sale roto. En dev debe ser `http://localhost:8080`.
  - El router de `main` sigue con `createWebHashHistory`; hasta que se mergee el PR #35 (history mode), `/reset-password?token=...` cae en el home.
- **El interceptor de 401 se come el error del token.** Los confirm devuelven `401 TOKEN_INVALID_OR_EXPIRED`. `applyAuthInterceptor` trata todo 401 como sesión vencida: intenta un refresh y rechaza con el error del refresh, así que la vista no puede decir "el enlace venció". Los dos confirm van en `AUTH_ENTRYPOINTS`.
- **Endpoints y API:** `usersEndpoints.ts` solo tiene `resetPasswordRequest`. Faltan:
  - `reset-password/confirm`, que manda el token como `Authorization: Bearer <token>` y en el body `{ new_password, confirm_password }`;
  - `reactivation/request`, con `{ email }`, que siempre responde 202;
  - `reactivation/confirm`, con el token también en Bearer.
- **Rutas:** las que arma el back son `/reset-password` y `/reactivate`, sin `requiresAuth`. La `ResetPasswordView` actual está en `/forgot-password` y en realidad pide el reset: conviene renombrarla a `ForgotPasswordView`.
- **No hay forma de llegar a la reactivación.** El login de una cuenta desactivada responde `INVALID_CREDENTIALS`, igual que una password mala, a propósito para no revelar cuentas. Hace falta un link en el login ("¿Desactivaste tu cuenta?") hacia una vista que pida el email, con un mensaje neutro.
- **Token en la URL:** al montar la vista hay que leerlo del query y quitarlo con `router.replace`, para que no quede en el historial ni salga en el `Referer` hacia scripts de terceros (Google Maps se carga desde `index.html`).
- **Estados de la vista:**
  - token inválido o vencido, con un link para pedir otro;
  - `PASSWORDS_DO_NOT_MATCH`, validado también en el cliente;
  - éxito: el confirm no setea cookies, así que redirige al login con un aviso.

## Open questions
- Valores reales de `SMTP_HOST` y `SMTP_FROM`: proveedor, o Mailpit en el compose (`mailpit:1025`).
- Rutas de la vista para pedir la reactivación (por ejemplo `/reactivate/request`).

## Next steps
- Arreglar `FRONT_BASE_URL` en `backend/users-service/.env.dev`.
- Mergear el PR #35.
- Front: endpoints, funciones de API, `AUTH_ENTRYPOINTS`, rutas y las tres vistas (confirmar reset, pedir reactivación, confirmar reactivación), y el link desde el login.
- Pasar `BREVO_API_KEY` a `SMTP_*` en `.env.local.example` y en el `README.md`.
