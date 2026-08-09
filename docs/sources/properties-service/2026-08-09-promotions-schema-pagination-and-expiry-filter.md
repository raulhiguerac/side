---
title: Promociones — schema propio, paginación, y el vencimiento filtrado en lectura
captured-from: conversation
captured-on: 2026-08-09
participants: [author, claude]
---

## Context

Al cablear la tab de promociones quedó claro que los endpoints no servían para
mostrar una promoción: los dos GET devolvían `PropertyCardSchema`, que solo sabe
decir si algo está promocionado. Revisándolos aparecieron un endpoint sin uso con
un bug de cache y el hecho de que nada expira las promociones vencidas.

## Key conclusions

- **`GET /admin/properties/{id}/promotions` se borra, no se deprecia.** Devolvía
  una lista de un solo elemento con la card de la property —nunca las
  promociones— o sea la misma respuesta que ya da `is_promoted`. Sin
  consumidores, deprecarlo dejaba armada la mina: leía y escribía
  `cache_property` con el schema equivocado, así que una llamada desde `/docs`
  envenenaba el cache del detalle público. Se fueron con él el UC, su dependencia
  y `get_all_by_property_id`.
- **`GET /admin/promotions` devuelve `AdminPromotionsPage`** con
  `AdminPromotionSchema` (`id`, `property_id`, `priority`, `starts_at`,
  `ends_at`, `is_active` y la card anidada). Sin eso, una tabla de promociones no
  puede mostrar prioridad ni vencimiento, que es lo único que la promoción
  decide.
- **Ese listado dejó de cachear.** Leía y escribía `feed_ads_global()`, la key de
  ads del feed público: cambiarle la forma a la respuesta la habría envenenado
  para todos los lectores del feed. Es una lectura interna y de pocas filas, no
  amerita cache propia.
- **Pagina por offset** (mismo criterio que `adr-admin-offset-pagination`: tabla
  chica, lectura interna, FK a la tabla grande), ordenado por `priority desc,
  ends_at asc, id`. El `id` desempata: sin orden total, el offset repite o
  saltea filas entre páginas.
- **`promoted_days` acepta `le=60`.** El tope existía solo en el front; una
  promoción es una campaña, no un estado permanente.
- **Los ads del feed se invalidan también al cambiar status y al borrar la
  property.** Faltaba en `SetPropertyStatusUseCase` (ítem conocido) y en
  `DeletePropertyUseCase` (no estaba anotado). Se invalidan siempre, sin
  averiguar antes si estaba promocionada: esa consulta costaría una query por
  cada escritura, y borrar una key que se repuebla sola sale más barato.
- **Nada expira las promociones vencidas.** `is_active` sigue en `True` pasado
  `ends_at`, así que una campaña vencida seguía contando como ad pago. Mitigado
  filtrando la fecha en cada lectura con `active_promotion_clause()`
  (`models/promotion.py`): `is_active AND ends_at > now()`.
- **La condición se define una sola vez** y la usan las cinco consultas que
  deciden "vigente" —listado admin, `count`, guard de duplicados, filtro
  `is_promoted` y join de ads— más la relación `Property.promotions`, que la
  necesita como string porque el `primaryjoin` se evalúa en el mapper. Escribirla
  suelta en cada query era reproducir el drift que se acababa de eliminar con las
  transiciones.
- **`func.now()` y no `datetime.now()`**: se resuelve en Postgres al correr la
  query; la versión Python quedaría congelada en el import del módulo.
- **El predicado vive en `models/`, no en `services/shared/helpers/`** — un
  modelo importando de servicios invierte la dependencia.

## Open questions

- Una promoción vencida ya no se puede quitar por el DELETE (404), porque
  `get_active_by_property_id` también filtra por fecha: la fila queda
  `is_active=True` invisible hasta que exista el job.
- La condición queda escrita dos veces (expresión y string del `primaryjoin`) y
  pueden divergir; mitigado teniéndolas pegadas en el mismo archivo.
- El `le=60` es un cambio de contrato: un cliente que mande 90 días pasa a
  recibir 422. Hoy no hay ninguno además del panel.

## Next steps

- Job que marque `is_active=False` al vencer — properties-service no tiene
  scheduler; el precedente es el APScheduler in-process de users-service. Recién
  ahí el filtro de fecha se vuelve redundante.
- Cubrir con tests el listado paginado y el filtro de vencimiento.
