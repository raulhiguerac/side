---
inclusion: always
---

# Invariantes del dominio

Reglas que el código tiene que cumplir siempre. Si encuentras código que las viola, es un **bug**, no una mejora. Entre paréntesis, el ADR o la página de la wiki que explica el porqué.

## Transversales

- Todo endpoint `/admin` exige `require_admin` (a nivel router o por endpoint). Un `/admin` sin ese chequeo es un bug de seguridad.
- La identidad sale del JWT de Keycloak; los casos de uso reciben el principal ya validado y nunca leen tokens (`adr-auth-keycloak-jwt`).
- Redis es opcional: si falla, el request no falla y se lee de la DB. Toda operación de cache va envuelta para degradar en silencio (`adr-cache-optional-layer`).
- Toda escritura invalida o refresca **todas** las claves de cache que dependen del dato: la entidad y las listas que la contienen.
- Los repositorios son síncronos: desde un caso de uso async se llaman con `await run_in_threadpool(partial(repo.metodo, ...))`. Un `await` directo sobre un repo, o llamar al repo dentro de `run_in_threadpool(...)` sin `partial`, es un bug.
- Los errores de DB se traducen con `translate_db_error`; después de un fallo de escritura va `rollback()` antes de relanzar.
- Las escrituras con varios pasos (DB + IdP, DB + storage) definen qué pasa si falla el segundo paso: compensación o rollback explícito.

## catalog-service

- `search_name` es el nombre normalizado (NFKD, sin tildes, minúsculas, sin espacios en los extremos) y se recalcula en cada escritura del nombre.
- `AdminDivision` es de un solo nivel, sin recursión (`adr-admin-division-single-level`).
- Listado admin de barrios: `count_all` aplica exactamente los mismos filtros que `get_all`; `get_coverage` aplica los mismos **salvo** `has_geometry`.
- Las lecturas admin no usan cache; las públicas (`geo_catalog`) sí, y solo devuelven activos.
- El área se calcula sobre la geometría original como `geography` (m²), nunca sobre la simplificada ni en grados.
- El bbox de vecinos se valida en el schema: rangos, `min < max` y lado ≤ 0.135°.
- `H3_RESOLUTION` no se cambia sin recomputar los `h3_index` existentes (`adr-h3-resolution-per-use-case`).

## properties-service

- Una fila de `Property` es una oferta con un solo `listing_type` (`adr-single-listing-type-per-property`).
- Cambiar las fotos de una propiedad verificada la devuelve a la cola de verificación.
- `verified` no es terminal; bajar una publicación es `ListingStatus active → inactive`, no un estado de verificación (`adr-verification-reversible-lifecycle`).
- Las transiciones legales las calcula el backend y las publica en el detalle; el front no las duplica (`adr-transitions-served-by-backend`).
- El precio estimado admin y el del ML viven en columnas separadas y ninguno pisa al otro (`adr-estimated-price-dual-signal`).
- El bulk create es idempotente por `external_id` determinístico (`adr-bulk-idempotent-external-id`).
- La ubicación (barrio) se resuelve al escribir el listing y se persiste; los consumidores no la vuelven a resolver (`adr-geo-enrichment-at-write-time`).
- El listado admin pagina por offset con `total`; el feed, con cursor opaco (`adr-admin-offset-pagination`, `adr-feed-opaque-cursor`).

## users-service

- Registro como saga: primero Keycloak, después DB; si falla la DB, se borra el usuario de Keycloak (`adr-keycloak-saga-compensation`).
- La desactivación es soft: `is_active=False`, Keycloak conserva el usuario (`adr-soft-deactivation`).
- Los action tokens son de un solo uso: se consumen con `GETDEL` y se guardan hasheados (`adr-action-tokens-redis`).

## frontend

- En el panel admin, la URL es la fuente de verdad de los filtros: la petición sale de un `watch` sobre la query, nunca del clic (`adr-admin-filters-in-query-params`).
- Una respuesta vieja nunca pisa a una nueva: toda carga que dependa de una selección o de un filtro descarta las respuestas fuera de orden.
- Las clases de Tailwind se escriben completas; nunca se arman concatenando strings.
