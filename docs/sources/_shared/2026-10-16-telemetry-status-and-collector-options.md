---
title: Estado de la telemetría de comportamiento y opciones para el collector
captured-from: conversation
captured-on: 2026-10-16
participants: [raul, claude]
---

## Context
El autor preguntó cómo funciona la telemetría y si para personalizar el feed hay que armar un webhook o un endpoint de ingesta. Se contrastó [[adr-impressions-beacon-pipeline]] (aceptado 2026-06-04) con el código actual. No se tomó ninguna decisión: lo de abajo son hallazgos y una propuesta.

## Key conclusions
- **No hay telemetría de comportamiento implementada.** No existe collector, ni topics `listing.impressed`/`listing.clicked`, ni captura en el front; `PropertyCardSchema` sigue sin ID de correlación ni posición por resultado.
- Kafka ya corre en el compose y analytics-service consume `listing-created` y produce `price-predicted` (`backend/analytics-service/.env.dev`); properties-service no produce a Kafka.
- **No es un webhook.** Un webhook es servidor→servidor; esto es navegador→servidor, de alto volumen y tolerante a pérdida: un endpoint collector que recibe beacons (`navigator.sendBeacon`), como fija el ADR.
- **Claim desactualizado en el ADR:** dice que `workers/` de properties-service solo contiene `__init__.py`; hoy tiene `bulk_create_properties_worker.py` (el worker del bulk import, que no es Kafka). Sigue sin haber consumer Kafka en properties.
- **Propuesta (sin aprobar), opción A:** el collector como ruta en properties-service, que sirve el feed y puede emitir el ID de correlación, con `session_id` anónimo; no suma un servicio al cluster de la demo y se puede extraer después sin cambiar el contrato (endpoint + topic). Costo: la carga de eventos comparte proceso con el feed.
- **Opción B:** servicio de ingesta dedicado; escala aparte pero es otro deployment desde el día uno.
- **Alternativa complementaria:** una herramienta de product analytics (p. ej. PostHog) da embudos y retención rápido, pero la señal para rankear el feed tiene que vivir en el sistema propio; no reemplaza el pipeline.
- Orden propuesto: (1) ID de correlación y posición en las cards del feed; (2) collector con `session_id` anónimo; (3) consumer en analytics que cuente impresiones y clicks por listing, que ya habilita "alcance de tu listing" para el dueño; el ranking personalizado después, con datos acumulados.

## Open questions
- ¿Opción A (ruta en properties-service) u opción B (servicio dedicado)?
- Schema del evento: el ADR propone `listing_id`, `correlation_id`, `position`, `session_id`, `event_type`, `ts`, `dwell_ms`.
- Cuándo y con qué consentimiento se pasa de `session_id` a `user_id`.

## Next steps
- Corregir el claim desactualizado del ADR sobre `workers/` de properties-service.
- Decidir A o B antes de escribir código.
