---
title: Change-password alineado con el back y reactivación de cuenta cableada
captured-from: conversation
captured-on: 2026-11-09
participants: [author, claude]
---

## Context
Quedaban dos flujos de cuenta del front sin cerrar: el cambio de contraseña en Ajustes siempre daba 422, y no había vista para reactivar una cuenta desactivada.

## Key conclusions
- **Change-password.**
  - `ChangePasswordPayload` manda `old_password`, como espera `ChangePassword` (`StrictBase`).
  - La lógica vive en `useChangePassword`, que devuelve `{ sending, error, changePassword }`. Traduce `INVALID_CREDENTIALS` a "La contraseña actual es incorrecta", `PASSWORD_SAME_AS_OLD` a su propio mensaje y un 422 a "Revisa la contraseña".
  - En éxito llama a `authStore.logout({ name: "login" })`, porque el back ya borró las cookies. `logout(to)` acepta el destino y por defecto sigue yendo a `/`.
- **Reactivación.**
  - Es una sola vista, `ReactivateAccountView` en `/reactivate`, que es el path que arma el back.
  - El composable `useReactivateAccount` captura el token al montar y lo quita con `router.replace`. El `v-if` decide con ese token capturado y no con `route.query`, para no cambiar de rama al limpiar la URL.
  - Con token: en `onMounted` confirma. Si sale bien, muestra "cuenta activa" y a los 2 s hace `replace` al login. Si falla, cualquier error vuelve al formulario con "El enlace no es válido o venció".
  - Sin token: el formulario pide el correo (`reactivation/request`, 202) y muestra un aviso neutro.
- **Link en el login.** "Reactivar cuenta" va en la misma fila que "¿Olvidaste tu contraseña?" (`justify-between`). Se descartaron un segundo "¿…?" debajo del registro, que se leía como una lista de FAQs, y el hint solo tras un login fallido.
- **Interceptor.** `reactivation/confirm` no está en `AUTH_ENTRYPOINTS`, por decisión del autor por ahora. Un token inválido gasta un refresh, y el composable no lee el `code`: trata cualquier fallo como enlace inválido.

## Open questions
- Ninguna.

## Next steps
- Agregar `reactivationConfirm` a `AUTH_ENTRYPOINTS` cuando se retome el front.
- Probar los dos flujos en el navegador contra el back.
