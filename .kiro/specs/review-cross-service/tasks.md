# Revisión de contratos entre servicios — tareas

- [ ] 1. properties → catalog: resolución por coordenadas (uno y en lote), qué hace properties si catalog cae o tarda, consistencia de `locality_id`/`city_id`.
- [ ] 2. properties → users: `POST /users/resolve` en el bulk, emails sin cuenta, tamaño del lote.
- [ ] 3. Kafka `listing_created`: quién lo produce, el schema del mensaje frente a lo que espera el consumer de analytics, qué pasa si nadie lo produce.
- [ ] 4. Auth entre servicios: issuer, audiencia, cookie y roles iguales en los cuatro servicios; `require_admin` consistente.
- [ ] 5. Front → backends: cada `types/` y cada llamada de `src/api/` contra el schema y la ruta reales (nombres, query params, paginación).
- [ ] 6. Cache entre servicios: datos de un servicio cacheados en otro (barrios en properties y en el front) y cuándo se invalidan.
- [ ] 7. Configuración compartida: puertos, URLs, CORS, timeouts y reintentos de los clientes HTTP.
- [ ] 8. Reporte con el formato de #review, con un hallazgo por frontera.
