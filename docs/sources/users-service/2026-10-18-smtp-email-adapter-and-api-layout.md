---
title: users-service manda correos por SMTP sin Brevo, y api/deps y api/routes se reorganizan
captured-from: conversation
captured-on: 2026-10-18
participants: [author, claude]
---

## Context
Con la cuenta de Brevo borrada y las plantillas ya en el repo, se quitó Brevo de users-service y el envío pasó a SMTP. Al cablear el adapter apareció provider duplicado en `api/deps`, y eso llevó a reorganizar deps y routes del servicio.

## Key conclusions
- **El caso de uso no cambia** (`request_reset_password.py` sigue llamando al mailer). El cambio va del mailer hacia abajo.
- **Port:** `EmailSenderPort` queda con un solo `send_email(to: list[str], subject, html_content, text_content)`.
  - Salen `send_template_email`, `template_id`, `sender`, `tags` y el `TypedDict` `EmailRecipient`.
  - `text_content` es obligatorio: cada correo va como `multipart/alternative` (txt + HTML), que ayuda con clientes sin HTML y con los filtros de spam.
- **Mailers:** `ResetPasswordMailer` y `ReactivationMailer` crean en su `__init__` un `Environment` de Jinja2 con:
  - `PackageLoader("app", "templates/email")`;
  - `select_autoescape(["html"])`;
  - `StrictUndefined`.

  Renderizan `.html` y `.txt` con el mismo contexto, y `ttl_minutes` sale de `CACHE_REACTIVATION_TTL_SECONDS // 60`. El asunto es una constante del mailer.
- **Adapter:** `SmtpEmailSenderAdapter` en `services/shared/adapters/`, sin capa de cliente aparte, porque `aiosmtplib` ya hace de cliente.
  - Usa `aiosmtplib.send()` (abre y cierra la conexión por envío) y no una instancia `SMTP` persistente: con `lru_cache` viviría todo el proceso, el servidor la cortaría por inactividad y no admite envíos concurrentes.
  - `use_tls` solo con el puerto 465; con el 587 aiosmtplib negocia STARTTLS solo.
  - Errores:
    - `SMTPAuthenticationError` → `SmtpMisconfiguredError` (nuevo, código `SMTP_MISCONFIGURED`);
    - cualquier otro `SMTPException` → `EmailSenderUnavailableError`.
- **Config inyectada:** el adapter recibe `host`, `port`, `username`, `password` y `sender` por constructor.
  - La dep lee y valida `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` y `SMTP_FROM`.
  - Si falta alguna o el puerto no es número, lanza `SmtpMisconfiguredError`.
  - Es el mismo patrón que las deps de storage.
- **Dependencias:**
  - entran `jinja2` y `aiosmtplib`;
  - salen `brevo-python`, `integrations/email/brevo/` y `brevo_email_sender_adapter.py`.
  - `uv add`/`uv remove` sincronizan el `.venv` con el lock y borran paquetes instalados a mano.
- **Layout de `api/deps`:**
  - los providers de infra con `lru_cache` van en `api/deps/shared/`, un archivo por tecnología: `cache`, `db`, `email`, `identity_provider`, `storage`;
  - los `*_use_cases.py` quedan solo con UoW, mailers y casos de uso;
  - se eliminan `get_cache_port` ×3, `get_email_sender` ×2 y `deps/storage.py`, que estaba muerto.
- **Layout de `api/routes`:** la carpeta sigue el prefix de la URL.
  - `account.py` pasa a `auth.py` (su prefix es `/auth`);
  - `user.py` se separa en `user/account.py` y `user/profile.py`;
  - `onboarding.py` queda plano porque su prefix es `/onboarding`.
  - Las 25 rutas expuestas son idénticas antes y después.
- **Health:** `routes/health.py` estaba vacío y sin montar. Ahora es igual al de los otros servicios y existe `GET /v1/health`.
- **Tests de integración:** corren con SQLite en memoria, sin servicios levantados. Con un solo `get_cache_port`, onboarding también queda con override de cache.
- **Consistencia entre servicios:** en properties y catalog los providers compartidos viven en el módulo del contexto principal (`listing.py`, `geo_catalog.py`) y los demás los importan de ahí. No tienen duplicados; pasarlos a `shared/` sería solo por consistencia.

## Open questions
- Valores de `SMTP_*` para dev y qué proveedor usar. Mailpit en el compose para local; con credenciales obligatorias necesita `MP_SMTP_AUTH_ACCEPT_ANY=1` y `MP_SMTP_AUTH_ALLOW_INSECURE=1`.
- Si properties y catalog adoptan `api/deps/shared/`.

## Next steps
- Poner `SMTP_HOST`, `SMTP_PORT` y `SMTP_FROM` en `.env.dev` y las credenciales en `.env.local`, y quitar `BREVO_API_KEY`.
- Actualizar el wiki de email (la página de Brevo pasa a SMTP) y cerrar en `open-items` los ítems del acoplamiento a Brevo, el `get_email_sender()` duplicado y el `TypeError` de `send_email`.
- Test del adapter SMTP que simule `aiosmtplib.send` y verifique cómo se traduce cada error.
