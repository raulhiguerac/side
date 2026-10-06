# Revisión de users-service — diseño

Dominios `auth` (registro, login, refresh, logout, cambio y reset de contraseña) y `user` (perfil, foto, onboarding, intereses, desactivación y reactivación, resolución de cuentas por email). Es el único servicio que escribe en Keycloak, y corre un worker de compensación con APScheduler.

Contexto: #[[file:docs/wiki/users-service/users-service.md]]

Orden: primero lo que cruza DB + Keycloak (si falla a la mitad, deja cuentas huérfanas), después tokens y sesiones, al final las lecturas de perfil.
