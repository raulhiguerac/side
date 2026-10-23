---
title: Integración users → email transaccional (SMTP)
status: draft
last-verified: 2026-10-18
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-auth]]"
  - "[[users-service-user]]"
  - "[[users-service-local-dev]]"
  - "[[open-items]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md, ../../../sources/users-service/2026-10-17-brevo-account-deleted-and-email-templates.md, ../../../sources/users-service/2026-10-18-smtp-email-adapter-and-api-layout.md]
---

## TL;DR

Los emails transaccionales (reset password y reactivación) se mandan por **SMTP** con `aiosmtplib`. Las plantillas viven **en el repo** y se renderizan con Jinja2. Los casos de uso llaman a un mailer, y el mailer manda por el port `EmailSenderPort`, que no sabe de proveedores. Cambiar de proveedor es cambiar las variables `SMTP_*`, no el código. Está en `draft` porque **todavía no hay proveedor ni valores de `SMTP_*` en dev**: hasta entonces, pedir reset o reactivación falla ([[open-items]]).

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `EmailSenderPort` | `services/shared/ports/email_sender.py` | Port (`Protocol`) con un solo método: `send_email(to, subject, html_content, text_content)`. `to` es una lista de correos. |
| `ResetPasswordMailer` | `services/auth/services/reset_password_mailer.py` | Renderiza `reset_password.{html,txt}` y define el asunto. |
| `ReactivationMailer` | `services/user/services/reactivation_mailer.py` | Renderiza `reactivation.{html,txt}` y define el asunto. |
| `SmtpEmailSenderAdapter` | `services/shared/adapters/smtp_email_sender_adapter.py` | Implementa el port con `aiosmtplib`. Recibe la config por constructor. |
| `get_email_sender()` | `api/deps/shared/email.py` | Lee y valida `SMTP_*` y arma el adapter. Es la única definición, con `lru_cache`. |
| Plantillas | `templates/email/` | `reset_password` y `reactivation`, cada una en `.html` (estilos inline) y `.txt`. |

No hay capa de cliente aparte: `aiosmtplib` ya cumple ese papel, así que el adapter lo usa directo.

## Plantillas y render

| Plantilla | Variables |
|---|---|
| `reset_password.{html,txt}` | `name`, `redirect_url`, `ttl_minutes` |
| `reactivation.{html,txt}` | `name`, `email`, `redirect_url`, `ttl_minutes` |

- Cada mailer crea en su `__init__` un `Environment` con `PackageLoader("app", "templates/email")`, `select_autoescape(["html"])` y `StrictUndefined`.
  - **Autoescape solo en `.html`**, porque `name` lo escribe el usuario. El `.txt` sale sin escapar.
  - Con `StrictUndefined`, una variable faltante falla en vez de mandar un hueco.
- `ttl_minutes` sale de `CACHE_REACTIVATION_TTL_SECONDS // 60`, el TTL que hoy comparten los dos tokens.
- El correo sale como `multipart/alternative`, con el txt primero y el HTML como alternativa. Así lo leen los clientes sin HTML, y los filtros de spam penalizan menos que un correo con solo HTML.
- **Origen del texto:** el de reset se recuperó de un correo recibido. El de reactivación es nuevo, porque no había copia cuando se borró la cuenta de Brevo.

## Flujo típico (reset password)

1. `RequestResetPasswordUseCase` genera el token y la `redirect_url` al frontend (`/reset-password?token=...`).
2. Busca el display name del destinatario con `email_recipients.get_display_name_by_account_id`.
3. Llama `ResetPasswordMailer.send_reset_password_email(email, name, redirect_url)`. El mailer renderiza las dos plantillas, el port recibe `send_email`, y el adapter abre una conexión SMTP, manda y la cierra.

## Configuración

| Variable | Uso |
|---|---|
| `SMTP_HOST`, `SMTP_PORT` | Servidor. Con `465` el adapter usa TLS directo; con otro puerto (normalmente `587`), `aiosmtplib` negocia STARTTLS si el servidor lo ofrece. |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Credenciales. Son secretos y van en `.env.local`. |
| `SMTP_FROM` | Remitente (`From`). |

Las cinco son obligatorias. Si falta alguna, o `SMTP_PORT` no es un número, `get_email_sender()` lanza `SmtpMisconfiguredError`. Como FastAPI resuelve la dep antes del endpoint, el request de reset o reactivación falla aunque la cuenta no exista. Para el entorno local ver [[users-service-local-dev]].

**Por qué `aiosmtplib.send()` y no una conexión persistente:** se manda un correo suelto por request. Una instancia de `SMTP` guardada en el adapter (que vive todo el proceso por el `lru_cache`) la cortaría el servidor por inactividad, y una misma conexión no admite dos envíos a la vez.

## Errores

| Situación | Excepción | Código |
|---|---|---|
| Falta una `SMTP_*` o el puerto no es un número | `SmtpMisconfiguredError` | `SMTP_MISCONFIGURED` |
| El servidor rechaza las credenciales (`SMTPAuthenticationError`) | `SmtpMisconfiguredError` | `SMTP_MISCONFIGURED` |
| Cualquier otro `SMTPException` (conexión, timeout, destinatario rechazado) | `EmailSenderUnavailableError` | `EMAIL_SENDER_UNAVAILABLE` |

Ninguno de los dos códigos está en `ERROR_CODE_TO_HTTP_STATUS`, así que responden 500. El handler genérico de `BaseError` devuelve el `context` en el body. Eso expone al cliente los nombres de variables, el host y el motivo del servidor SMTP, y como solo se manda correo a cuentas activas, también distingue si la cuenta existe ([[open-items]]). `EmailSenderMisconfiguredError` quedó sin uso.

## Historia: Brevo (hasta 2026-10)

Hasta 2026-10 el envío iba por la API de Brevo (`brevo-python`), con plantillas guardadas en el dashboard de Brevo y referenciadas por id (`2` reset, `1` reactivación). El port tenía `send_template_email(template_id: int, ...)`. Brevo **borró la cuenta Free por inactividad**: su regla es 4 meses sin uso, con avisos a 30, 15, 7 y 1 día. Con la cuenta se perdieron las plantillas. Se rehicieron en el repo y se quitaron el SDK, el cliente y el adapter de Brevo. Con eso se cerraron también el `get_email_sender()` duplicado y un `TypeError` latente del adapter viejo.

## Claims

- El port declara un solo método, `send_email(to: list[str], subject, html_content, text_content)` ([email_sender.py:4-13](backend/users-service/src/app/services/shared/ports/email_sender.py#L4-L13)).
- Los mailers renderizan con `PackageLoader("app", "templates/email")`, autoescape para HTML y `StrictUndefined` ([reset_password_mailer.py:12-16](backend/users-service/src/app/services/auth/services/reset_password_mailer.py#L12-L16), [reactivation_mailer.py:12-16](backend/users-service/src/app/services/user/services/reactivation_mailer.py#L12-L16)).
- `ttl_minutes` se calcula como `CACHE_REACTIVATION_TTL_SECONDS // 60` en los dos mailers ([reset_password_mailer.py:22](backend/users-service/src/app/services/auth/services/reset_password_mailer.py#L22), [reactivation_mailer.py:23](backend/users-service/src/app/services/user/services/reactivation_mailer.py#L23)).
- Las plantillas están en el repo, cada una en `.html` y `.txt` ([templates/email/](backend/users-service/src/app/templates/email)).
- El adapter arma un `EmailMessage` con el txt como contenido y el HTML como alternativa ([smtp_email_sender_adapter.py:21-26](backend/users-service/src/app/services/shared/adapters/smtp_email_sender_adapter.py#L21-L26)).
- El adapter usa `aiosmtplib.send` con TLS directo solo en el puerto 465 ([smtp_email_sender_adapter.py:29-36](backend/users-service/src/app/services/shared/adapters/smtp_email_sender_adapter.py#L29-L36)).
- `SMTPAuthenticationError` se traduce a `SmtpMisconfiguredError` y el resto de `SMTPException` a `EmailSenderUnavailableError` ([smtp_email_sender_adapter.py:37-46](backend/users-service/src/app/services/shared/adapters/smtp_email_sender_adapter.py#L37-L46)).
- `get_email_sender()` exige `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` y `SMTP_FROM`, y lanza `SmtpMisconfiguredError` si falta alguna o el puerto no es número ([email.py:10-22](backend/users-service/src/app/api/deps/shared/email.py#L10-L22)).
- `get_email_sender()` está definida una sola vez y la importan las deps de auth y de user ([email.py:13-14](backend/users-service/src/app/api/deps/shared/email.py#L13-L14), [auth_use_cases.py](backend/users-service/src/app/api/deps/auth_use_cases.py), [user_use_cases.py](backend/users-service/src/app/api/deps/user_use_cases.py)).
- Los UCs envían a través de los mailers, no del adapter directo ([request_reset_password.py:56](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L56), [request_account_reactivation.py:83](backend/users-service/src/app/services/user/use_cases/account/request_account_reactivation.py#L83)).
- `jinja2` y `aiosmtplib` son dependencias directas y `brevo-python` ya no está ([pyproject.toml:26-27](backend/users-service/pyproject.toml#L26-L27)).
- El handler de `BaseError` responde 500 a los códigos que no están en el mapa y devuelve `context` en el body ([exception_handlers.py:62-83](backend/users-service/src/app/api/handlers/exception_handlers.py#L62-L83)).
- Los tokens de reset y de reactivación son de un solo uso: el confirm los lee con `getdel_json` ([confirm_reset_password.py:63](backend/users-service/src/app/services/auth/use_cases/confirm_reset_password.py#L63), [reactivate_current_account.py:51](backend/users-service/src/app/services/user/use_cases/account/reactivate_current_account.py#L51)).
