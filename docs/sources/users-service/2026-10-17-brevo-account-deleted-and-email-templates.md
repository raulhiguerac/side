---
title: La cuenta de Brevo se borró por inactividad y las plantillas de correo pasan al repo
captured-from: conversation
captured-on: 2026-10-17
participants: [author, claude]
---

## Context
Revisando qué tan acoplado está users-service a Brevo (port y wiring en [[users-service-email-brevo]]), salió que las plantillas solo existían en el dashboard de Brevo. Brevo borró la cuenta Free por inactividad y las plantillas se perdieron. El texto del reset se recuperó de un correo recibido; el de reactivación no.

## Key conclusions
- **Política de Brevo:** las cuentas Free sin uso durante 4 meses se borran de forma permanente, con avisos a 30, 15, 7 y 1 día. Iniciar sesión, mandar transaccionales o tener automatizaciones cuenta como actividad. Los términos de uso (versión 2025-10-01) hablan de 6 meses; para Free manda la regla de 4 meses del centro de ayuda.
- **Estado hoy:** la `BREVO_API_KEY` de `.env.local` ya no sirve, así que pedir reset o reactivación termina en `EmailSenderUnavailableError`. Los dos flujos están caídos hasta tener proveedor nuevo.
- **Las plantillas pasan al repo**, en `backend/users-service/src/app/templates/email/`: `reset_password.{html,txt}` y `reactivation.{html,txt}`. El reset sale del correo recuperado; la reactivación es texto nuevo. Es el núcleo de la opción B de [[open-items]].
- **Contrato de variables:** `name`, `redirect_url` y `ttl_minutes`; la reactivación además usa `email`. `ttl_minutes` sale de `CACHE_REACTIVATION_TTL_SECONDS // 60`, que hoy usan los dos flujos (900 s).
- **Cambios respecto al original:** la expiración es variable (antes decía "15 minutos" fijo) y hay un enlace de respaldo bajo el botón. El botón usa `#15803D` (`primary-strong`).
- **Se verificó** que los dos tokens son de un solo uso (`getdel_json` en `confirm_reset_password.py` y `reactivate_current_account.py`), así que el aviso del correo es cierto.
- **Render verificado** con Jinja2 en modo estricto: no falta ninguna variable, el HTML escapa `name` y la URL, el `.txt` no escapa.
- **Free tiers comparados** (fuentes de terceros, octubre 2026; varias se contradicen): Brevo 300/día, Mailjet 6.000/mes con tope de 200/día (una sola fuente), Resend 3.000/mes con tope de 100/día, SMTP2GO 1.000/mes, MailerSend 500/mes con aprobación y tarjeta, Postmark 100/mes, SES según la cuenta, SendGrid sin free tier permanente. Para dos transaccionales cualquiera alcanza; pesan más el soporte SMTP y el dominio verificado.

## Open questions
- Qué proveedor usar: Brevo de nuevo por SMTP o cambiar.
- El remitente y el `Reply-To`: los correos dicen "responde este correo", lo que solo vale si es un buzón que alguien lee. Con `no-reply@` hay que cambiar la frase.
- Si el verde de los botones del front cambia, alinear el del correo.

## Next steps
- Del autor, en el back:
  - adapter SMTP (`aiosmtplib`) con host, puerto, credenciales y remitente por env;
  - mailers que rendericen con un `Environment` de Jinja2 con `autoescape=select_autoescape(["html"])` y los asuntos definidos ahí;
  - sacar `send_template_email` y `template_id` del port;
  - un solo `get_email_sender()`;
  - Jinja2 como dependencia directa (hoy solo es transitiva en `uv.lock`);
  - quitar `brevo-python`.
- Crear la cuenta del proveedor elegido, verificar el dominio (SPF, DKIM y DMARC en Cloudflare) y poner las credenciales en `.env.local`.
