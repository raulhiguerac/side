---
title: Cobertura del MVP — prometido vs construido
status: stable
last-verified: 2026-10-04
owners: [product]
sources: []
---

# Cobertura del MVP — prometido vs construido

## 1. Veredicto

**Casi.** El MVP de `side` está construido punta a punta en lo que de verdad importa para el usuario: buscar propiedades (feed lista + mapa), publicar y gestionar listings propios, pedir un avalúo online (`/predict`), y un panel admin de moderación/promociones/importaciones/catálogo que la propia wiki subestima. Los cuatro backends tienen sus dominios cableados y el frontend consume endpoints reales, no mocks. **Lo que impide declararlo "completo" es un solo flujo del AVM que no cierra y un puñado de bugs de corrupción de datos sobre casos de uso que sí existen:** (a) el AVM asíncrono properties↔analytics no está conectado — analytics calcula y emite el precio, pero nadie en properties lo consume, así que el precio estimado nunca llega al listing ni se muestra en ningún lado; (b) un re-import de bulk pisa el estado de moderación; (c) el worker Kafka de analytics ni siquiera se levanta en el arranque, y cuando se levante no es idempotente (duplica predicciones y eventos). El AVM "manual" (admin escribe un precio) también es write-only: no hay schema ni UI que lo lea.

Dicho simple: **el comprador busca, el vendedor publica, el admin modera y el avalúo online responde — todo eso anda. Lo que no anda es el diferenciador central del producto: que el AVM alimente el listing automáticamente.**

---

## 2. El MVP según la doc

Destilado de las fuentes de alcance, con el roadmap-2026 como autoridad cuando hubo que desempatar.

Fuentes:
- `docs/wiki/_shared/project-roadmap-2026.md` (autoridad del alcance, fases 1–3 = MVP; 4–5 = post-MVP)
- `docs/sources/_shared/2026-05-29-project-roadmap.md` (roadmap original)
- `docs/sources/_shared/2026-06-09-mvp-audit-scores.md` (auditoría previa con scores)
- `docs/wiki/_shared/business-model.md` (monetización por fase; separa MVP de futuro)
- `docs/wiki/_shared/open-items.md` (gaps/deuda reconocidos)

Casos de uso que constituyen el MVP (fases 1–3 del roadmap):

**Fase 1 — Catálogo + Onboarding** (marcada ✅)
1. Catálogo geográfico: CRUD países→divisiones→localidades→barrios, geo-resolution `(lat,lon)→barrio`, POIs, PostGIS, Redis.
2. Identidad: registro + sesión Keycloak, onboarding de 4 pasos con intereses, soft-deactivation.
3. Frontend: landing, modal de onboarding, selector de localidad conectado al catálogo.

**Fase 2 — Properties** (marcada 🔄)
4. Modelos de listing (5 tablas PostGIS+H3), UCs de listing, imágenes presigned batch.
5. Feed de búsqueda con cursor opaco + Redis cache-aside; feed lista y feed mapa (bbox).
6. Bulk import de Bogotá (IDECA) — seed de inventario.
7. Frontend: vista detalle `/listing/:id` (galería, info, mapa) — **precio estimado marcado ⏳**.
8. Frontend: formulario publicar + subir imágenes + gestionar mis listings.
9. Frontend: MapView con Leaflet + bbox + paginación.
10. Frontend: panel de moderación admin — aprobar/rechazar listings — **marcado ⏳**.

**Fase 3 — AVM / Analytics** (marcada ✅)
11. Pipeline ML: LightGBM + Optuna, modelo `bogota-avm @production` en MLflow.
12. analytics-ms: dominio de predicción, DI, Alembic, endpoint `/predict` online.
13. analytics-ms: worker Kafka batch (listings → predicciones) — **marcado ⏳ "off by default"**.
14. Frontend AVM: form multi-step, GMaps Places, mapa reactivo, cableo a `/predict`.
15. Re-registrar modelo con `year_built` nullable — **marcado ⏳**.

**Contradicción entre fuentes (declarada):** el roadmap-2026 marca la Fase 3 completa ✅, pero dentro de ella deja el worker Kafka (ítem 13) en ⏳; `mvp-audit-scores` (2026-06-09) ya lo señalaba como gap. Tomo el roadmap-2026 como autoridad: el worker es parte del MVP de la Fase 3 y sigue sin cerrarse. Además, `project-roadmap-2026.md` marca el panel de moderación (ítem 10) como ⏳ y el precio estimado en el detalle (ítem 7) como ⏳ — y aquí **la wiki está desactualizada en sentido opuesto para el panel**: el código tiene el panel admin completo (ver §3). El precio estimado, en cambio, sigue sin existir de cara al usuario (confirmado en código).

> Nota: `docs/wiki/frontend/frontend.md` afirma que solo Login/Register funcionan — es falso. El router monta detalle, create, edit, my-properties, settings, perfil público y todo el panel admin. Se usó el código como verdad.

---

## 3. Cobertura por caso de uso

Estado: **Completo** = backend UC + endpoint + (si es de cara al usuario) pantalla front cableada. **Parcial** = falta un extremo o hay un bug conocido que lo degrada. **Ausente** = no hay implementación.

### Journey: Catálogo + Onboarding (Fase 1)

| Caso de uso | Estado | Evidencia | Nota |
|---|---|---|---|
| CRUD geográfico + geo-resolution + POIs | Completo | `catalog-service/.../api/routes/{countries,localities,neighborhoods,geo_resolution}.py`; `services/geo_catalog/use_cases/*`, `services/geo_resolution/use_cases/*` | Isócronas (`resolve_isochrone.py`) también implementadas (era diferenciador, ya cerrado). |
| Registro + sesión Keycloak | Completo | `users-service/.../services/auth/use_cases/{register_account,authenticate_account,logout}.py`; routes `account.py` | — |
| Onboarding 4 pasos + intereses | Completo (con bug de cache) | `users-service/.../services/user/use_cases/onboarding/*`; route `onboarding.py` | Bug alta: la invalidación de cache nunca corre (`delete` posicional vs keyword-only, tapado por `except: pass`). Ver §5. |
| Soft-deactivation de cuenta | Parcial | `services/user/use_cases/account/deactivate_current_account.py` | No propaga a los listings del usuario — quedan visibles en el feed tras desactivar (open-items). Fuera del happy path del MVP pero es inconsistencia conocida. |
| Front: landing + onboarding + selector de localidad | Completo | `frontend/src/views/public/HomeView.vue`, componentes de onboarding, `catalogApi.ts` | — |

### Journey: El vendedor publica y gestiona (Fase 2)

| Caso de uso | Estado | Evidencia | Nota |
|---|---|---|---|
| Crear listing | Completo | `listing/use_cases/property_core/create_property.py`; route `POST /v1/properties`; `frontend/.../properties/create/CreatePropertyView.vue` | — |
| Subir imágenes (presigned batch) | Completo | `listing/use_cases/images/{request_presigned_urls,confirm_image_uploads}.py`; routes `/images` | — |
| Editar / borrar / visibilidad | Completo | `property_core/{update_property,delete_property,set_property_visibility}.py`; `frontend/.../properties/edit/EditPropertyView.vue` | — |
| Mis listings (`/properties`) | Completo | `GET /v1/properties/me` → `get_my_properties.py`; `frontend/.../properties/dashboard/MyPropertiesView.vue`; endpoint `PROPERTIES_ENDPOINTS.me` | Front y back coinciden en `/me`. |
| Detalle público `/listing/:id` | Completo | `GET /v1/properties/{id}` → `get_property.py`; `frontend/.../properties/detail/PropertyDetailView.vue`; ruta `property-detail` | Galería + mapa presentes. El **precio estimado NO** aparece (ver fila AVM→listing). |
| Perfil público del publicante | Completo (básico) | `GET /v1/properties/users/{user_id}` (paginado offset) → `get_public_user_properties.py`; `frontend/.../public/PublicProfileView.vue` | Perfil público real (bio/rating) es post-MVP. |

### Journey: El comprador busca (Fase 2)

| Caso de uso | Estado | Evidencia | Nota |
|---|---|---|---|
| Feed lista (cursor + cache + ads) | Completo | `search/use_cases/get_feed.py`; route `search.py`; `frontend/.../feed/FeedView.vue` + `PropertiesView.vue` | Intercalado de promocionados implementado. |
| Feed mapa (bbox) | Completo | `search/use_cases/get_feed_map.py`; `frontend/.../feed/MapView.vue` (Leaflet) | — |
| Seed de inventario Bogotá | Completo (con caveats de datos) | `workers/bulk_create_properties_worker.py`; smoke test 20k (open-items) | 18.744 filas quedaron en `unverified` (migración de datos pendiente). Los dos seeds viejos (500/5k) no tienen `external_id`/`email` y fallarían. |
| Score de oportunidad inline en card | Ausente (post-MVP) | — | Fase 5. Depende del AVM→listing. |

### Journey: El admin modera y mantiene (Fase 2)

| Caso de uso | Estado | Evidencia | Nota |
|---|---|---|---|
| Panel de moderación (aprobar/rechazar/estado) | Completo | `admin.py` routes `/properties/{id}/status` y `/verification`; `moderation/{set_status,verify}.py`; `frontend/.../admin/properties/moderation/AdminModerationView.vue` | La wiki lo marcaba ⏳; el código lo tiene completo con transiciones server-driven. |
| Promociones (crear/listar/borrar) | Completo (con deuda) | `promotions/{create,delete,list_all}.py`; routes `/promotions`; `frontend/.../admin/properties/promotions/*` | No expiran solas (falta job; mitigado por filtro de fecha en lectura). `GET /admin/promotions` sin filtros. |
| Importaciones bulk (presigned + job async) | Completo (con bug de re-import) | routes `/properties/bulk*`; `request_bulk_upload_url.py`, `bulk_create_properties.py`, `get_bulk_job_status.py`; `frontend/.../admin/properties/imports/AdminImportsView.vue` | Bug alta: re-import pisa estado de moderación. Ver §5. |
| Admin catálogo (barrios/localidades/países/divisiones) | Parcial | `catalog-service/.../api/routes/admin/*`; `services/catalog_admin/use_cases/*`; `frontend/.../admin/catalog/*` | Barrios: listado/detalle/vecinos + tab front ✅. Faltan los `GET` admin de localidades/divisiones/países (no se puede ver/reactivar lo desactivado); acciones de barrios (editar/geometría/desactivar) sin UI. |

### Journey: Avalúo (AVM, Fase 3)

| Caso de uso | Estado | Evidencia | Nota |
|---|---|---|---|
| Modelo AVM entrenado y promovido | Completo | `bogota-avm @production` en MLflow (roadmap) | Pendiente re-registrar con `year_built` nullable (workaround vigente). |
| Predicción online `/predict` | Completo | `analytics-service/.../api/routes/predict.py` → `prediction/use_cases/online.py` | Cableado y funcional. |
| Front AVM (form + GMaps + cableo /predict) | Completo | `frontend/.../avm/AvmView.vue`; `avmApi.ts` | — |
| Worker Kafka batch (listings → predicciones) | **Parcial** | `analytics-service/.../workers/listing_created/{runner,consumer}.py` existen, **pero `main.py` no los arranca** (sin lifespan/startup) | Off by default. Además no es idempotente: duplica predicciones y eventos en reproceso (Bug·alta, §5). |
| **AVM → listing (precio estimado llega a la propiedad)** | **Ausente (bloqueante)** | analytics emite a `KAFKA_PREDICTIONS_TOPIC` (`consumer.py:95`); properties `workers/` solo tiene `bulk_create_properties_worker.py` — **no hay consumer** del topic | `SetEstimatedPriceUseCase` existe pero su único caller es el router admin (`require_admin`); la rama `principal=None` para el path ML es código muerto. El loop async nunca cierra. |
| Precio estimado visible en el producto | **Ausente** | `estimated_price`/`ml_estimated_price` tienen **0 referencias** en `frontend/src`; no están en `PropertyCardSchema`/`PropertyDetailSchema`; el endpoint `estimated-price` no está en `propertiesEndpoints.ts` | Tanto el AVM manual (admin escribe) como el ML son write-only: nadie los lee. |

---

## 4. Gaps que bloquean el MVP (ordenados por impacto)

1. **El AVM nunca llega al listing (loop async roto).** analytics calcula el precio y lo emite por Kafka, pero properties no tiene consumer que lo reciba y llame `SetEstimatedPriceUseCase`. Es el diferenciador central del producto (avalúo automático) y hoy está desconectado. **Impacto: alto — el valor diferencial del MVP no existe de cara al usuario.** (`properties-service/.../workers/` sin consumer; open-items "Worker de properties que consume `price-predicted`".)

2. **El precio estimado no se puede leer desde ningún cliente.** Aunque se cableara el loop, `ml_estimated_price`/`admin_estimated_price` no están expuestos en ningún schema de salida ni consumidos por el front (0 referencias). El AVM manual del admin es write-only. **Impacto: alto — sin esto el avalúo no es visible aunque se calcule.**

3. **El worker Kafka de analytics no arranca.** `main.py` (`create_app`) no levanta `ListingWorkerRunner`; el pipeline batch está off por defecto. Prerrequisito del gap #1. **Impacto: alto.**

4. **Re-import de bulk pisa el estado de moderación.** `_PROPERTY_UPSERT_FIELDS` incluye `status`/`verification_status`; un re-import del mismo CSV revierte properties verificadas a `pending`, reactiva las dadas de baja y deja estados contradictorios (`pending` con `verified_by` poblado). **Impacto: medio-alto — corrompe el trabajo de moderación, que es un caso de uso del MVP.** (properties review 2026-10-04, Bug·alta.)

5. **Cobertura admin incompleta en catálogo.** Faltan los `GET` admin de localidades/divisiones/países: lo que un admin desactiva no se puede ver ni reactivar. **Impacto: medio — el admin puede dejar el catálogo en un estado del que no puede volver por UI.**

6. **Inventario del seed en estado inválido.** 18.744 filas quedaron en `unverified` (salto legal solo lo dispara el dueño, que en import no existe) → cola de moderación impracticable; los seeds viejos fallarían el 100% por faltar `external_id`/`email`. **Impacto: medio — el inventario del MVP no es moderable tal como quedó.**

---

## 5. Riesgos de calidad sobre lo ya construido

Incorporados de las auditorías de código de solo lectura (`docs/sources/<servicio>-service/2026-10-04-review.md`). Solo los que degradan un caso de uso del MVP:

- **analytics — flujo Kafka no idempotente (Bug·alta).** Commit de offset at-least-once + publicación de eventos + persistencia sin clave de deduplicación → un reproceso duplica filas de predicción en DB y eventos `price-predicted` aguas abajo. Degrada el caso de uso #13/AVM→listing incluso cuando se encienda. (`analytics review` Resumen.)
- **properties — re-import pisa moderación (Bug·alta).** Ya listado como gap #4. Afecta directamente el caso de uso de moderación.
- **users — invalidación de cache de onboarding rota (Bug·alta).** `invalidate_current_user_cache` llama `cache.delete(...)` posicional contra una firma keyword-only; el `TypeError` queda tapado por `except: pass`. Los cuatro flujos de onboarding nunca invalidan cache → perfil/intereses stale. (`users review` Resumen.)
- **users — writes de perfil sin wrapper de cache (Bug·media).** `update_current_profile`/`upload_profile_photo` devuelven 500 si Redis cae pese a haber comiteado en DB.
- **Pipeline de tests ciego para dos servicios del MVP.** El audit (`make audit`) crea el venv sin el extra `dev`, así que `pytest` no existe para **properties** ni **analytics**: un test rojo pasaría inadvertido. analytics además tiene `tests/integration/**` vacío (ninguna rebanada se ejercita extremo a extremo). Un caso de uso "implementado" pero sin señal verde de tests y con bug de corrupción de datos **no está listo**. (`properties review` Mejora·alta; `analytics review` Resumen.)

---

## 6. Fuera de alcance MVP (no son gaps)

Según el roadmap (fases 4–5) y el business-model, estos son post-MVP y no deben contarse como huecos del MVP:

- **Infra K3s/Helm/CI-CD** (Fase 4) — rama `infra/k8s` con issues conocidos; docker-compose es el entorno MVP.
- **Score de oportunidad inline, alertas de precio, feed personalizado por comportamiento, tracking de impresiones, búsqueda NLP con LLM** (Fase 5 — diferenciadores).
- **Heatmap desde DWH** (requiere DWH separado).
- **notifications-ms y payments-ms** — fase draft, sin código en el repo.
- **Monetización más allá de promocionados**: comisiones, B2B data, matching/roommates, FinTech (fases 3–4+ del business-model). Los **promocionados sí** están implementados y son MVP.
- **Observabilidad (logs/métricas/trazas), rate limiting del feed, cursor firmado HMAC** — hardening de producción, no casos de uso del MVP.

---

## 7. Qué falta para cerrar el MVP (accionable, priorizado)

1. **Cerrar el loop AVM→listing.** Añadir en properties-service un consumer Kafka del topic de predicciones que llame `SetEstimatedPriceUseCase` con `principal=None` (habilitar y testear ese path hoy muerto). Prerrequisito: arrancar el worker de analytics en `main.py` y hacerlo idempotente (clave de deduplicación por listing/versión antes de persistir y emitir).
2. **Exponer el precio estimado.** Agregar `ml_estimated_price`/`admin_estimated_price` a los schemas de salida (resolviendo el conflicto de la key de cache compartida), cablear el endpoint en `propertiesEndpoints.ts` y mostrarlo en el detalle (y luego en la card para el score de oportunidad, ya post-MVP).
3. **Arreglar el re-import de moderación.** Sacar `status`/`verification_status` de `_PROPERTY_UPSERT_FIELDS` (mantener fuera `verified_by`/`rejection_reason`); el re-import debe refrescar datos del inmueble sin tocar el ciclo de vida. Agregar el test de upsert sugerido.
4. **Arreglar la invalidación de cache de onboarding** (pasar `key=` por keyword) y envolver los writes de perfil para degradar si Redis cae.
5. **Completar admin de catálogo**: `GET` admin de localidades/divisiones/países y acciones de barrios en la UI.
6. **Sanear el inventario del seed**: `UPDATE ... SET verification_status='pending' WHERE verification_status='unverified'` (script o migración); regenerar/retirar los seeds viejos sin `external_id`/`email`; definir criterio de priorización de la cola.
7. **Arreglar el pipeline de tests**: instalar el extra `dev` en el audit para que properties y analytics corran pytest; agregar tests de integración mínimos a analytics.
8. (Menor) Re-registrar el AVM con `year_built` nullable para quitar el workaround.

Con los puntos 1–4 resueltos el MVP pasa de "casi" a "sí": los tres son flujos que ya tienen casi toda la pieza construida y fallan en el último empalme.
