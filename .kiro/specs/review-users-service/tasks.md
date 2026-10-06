# Revisión de users-service — tareas

- [ ] 1. Leer `audit-report.txt` (users-service) y los pendientes de users en `open-items.md`.
- [ ] 2. Registro (`POST /auth/register`): saga Keycloak → DB, compensación si falla la DB, email duplicado, carreras entre dos registros iguales.
- [ ] 3. Worker de compensación (`workers/keycloak_tasks.py`): idempotencia, qué pasa si Keycloak no responde, `max_instances` y solapamiento.
- [ ] 4. Login, refresh y logout: cookies (flags, expiración), cuenta desactivada, errores de Keycloak traducidos.
- [ ] 5. Cambio y reset de contraseña: action tokens de un solo uso (`GETDEL`, hash), expiración, enumeración de usuarios por mensajes distintos.
- [ ] 6. Desactivación y reactivación: soft delete, qué endpoints siguen aceptando la cuenta desactivada, tokens de reactivación.
- [ ] 7. Perfil y foto (`/users/me/profile`, `/photo`): validación, subida a storage, limpieza de la foto anterior, perfiles públicos (`/users/profiles/{id}`) sin datos privados.
- [ ] 8. Onboarding e intereses: validación contra catalog, escrituras parciales.
- [ ] 9. `POST /users/resolve` (lo usa properties-service): autorización, límites del lote, emails sin cuenta activa.
- [ ] 10. Transversal: validación del JWT, `require_admin` donde corresponda, cache opcional, CORS.
- [ ] 11. Tests y reporte con el formato de #review.
