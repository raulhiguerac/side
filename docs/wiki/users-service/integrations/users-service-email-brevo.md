---
title: Integración users → Brevo (email transaccional)
status: draft
last-verified: 2026-05-28
owners: [users-service]
related:
  - "[[users-service]]"
  - "[[users-service-auth]]"
  - "[[users-service-user]]"
sources: [../../../sources/users-service/2026-05-28-foundational-exploration.md]
---

## TL;DR

Los emails transaccionales (reset password, reactivación) se mandan vía **Brevo** con `brevo-python`. El `EmailClient` soporta email HTML directo y por template. Los UCs no lo usan directo: pasan por mailers (`ResetPasswordMailer`, `ReactivationMailer`) detrás del port `EmailSender`.

## Componentes

| Pieza | Archivo | Rol |
|---|---|---|
| `EmailClient` | `integrations/email/brevo/client.py` | Wrapper sobre `TransactionalEmailsApi` de Brevo. |
| `BrevoEmailSenderAdapter` | `services/shared/adapters/brevo_email_sender_adapter.py` | Implementa el port `EmailSender`. |
| `EmailSender` | `services/shared/ports/email_sender.py` | Port que ven los mailers. |
| `ResetPasswordMailer` | `services/auth/services/reset_password_mailer.py` | Arma y envía el email de reset. |
| `ReactivationMailer` | `services/user/services/reactivation_mailer.py` | Arma y envía el email de reactivación. |

## Métodos del cliente

- `send_email(sender, to, subject, html_content, tags)` — email HTML directo.
- `send_email_template(template_id, to, params, subject, tags)` — email por template de Brevo.

Ambos lanzan `EmailSenderUnavailableError` (con status/reason de Brevo en el context) ante un `ApiException`. El cliente falla en construcción con `EmailSenderMisconfiguredError` si falta la API key.

## Flujo típico (reset password)

1. `RequestResetPasswordUseCase` genera el token y la `redirect_url` al frontend (`build_redirect_url(FRONT_BASE_URL, "/reset-password", {token})`).
2. Pide el display name del destinatario vía `email_recipients.get_display_name_by_account_id`.
3. `ResetPasswordMailer.send_reset_password_email(email, name, redirect_url)` → adapter → `EmailClient`.

## Known gap — naming de la API key

El cliente lee la env var **`BREVO_API_KEY`** ([client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15)), pero el `.env.example` del servicio declara **`BREVO_SMTP_KEY`**. Hay que setear `BREVO_API_KEY` (no `BREVO_SMTP_KEY`) para que el envío funcione — ver [[users-service-local-dev]].

## Claims

- El `EmailClient` usa `brevo_python.TransactionalEmailsApi` y falla si falta `BREVO_API_KEY` ([client.py:14-25](backend/users-service/src/app/integrations/email/brevo/client.py#L14-L25)).
- Soporta envío directo (`send_email`) y por template (`send_email_template`) ([client.py:27-86](backend/users-service/src/app/integrations/email/brevo/client.py#L27-L86)).
- Un `ApiException` de Brevo se traduce a `EmailSenderUnavailableError` con status/reason en el context ([client.py:46-54](backend/users-service/src/app/integrations/email/brevo/client.py#L46-L54)).
- El cliente lee `BREVO_API_KEY`, pero el `.env.example` declara `BREVO_SMTP_KEY` — mismatch de naming ([client.py:15](backend/users-service/src/app/integrations/email/brevo/client.py#L15), [backend/users-service/.env.example](backend/users-service/.env.example)).
- Los UCs envían a través de mailers detrás del port `EmailSender`, no del cliente directo ([request_reset_password.py:56-60](backend/users-service/src/app/services/auth/use_cases/request_reset_password.py#L56-L60)).
