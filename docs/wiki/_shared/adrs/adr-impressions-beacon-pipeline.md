---
title: ADR-0004 — Impresiones y clicks vía beacon de cliente + collector + Kafka
status: draft
last-verified: 2026-06-04
owners: [_shared, frontend, properties-service, analytics-service]
related: [[open-items]], [[properties-service-search]], [[frontend-architecture]], [[analytics-service]], [[architecture]]
sources: []
decision-date: 2026-06-04
decision-status: accepted
---

# ADR-0004 — Impresiones y clicks vía beacon de cliente + collector + Kafka

> Diseño forward-looking. Nada de esto está implementado al 2026-06-04 — el ítem vive en [[open-items]] ("Impresiones, analytics de comportamiento y feed personalizado"). Este ADR fija el **enfoque acordado** antes de escribir código, no documenta algo existente.

## Contexto

Para evolucionar el feed de "filtra por preferencias declaradas" a "rankea por comportamiento" (ver [[properties-service-search]] §Evolución), hace falta capturar señal implícita: **qué listings vio el usuario (impresión), cuánto, y cuáles clickeó**. Es alto volumen (cada scroll genera impresiones) y baja criticidad (perder un evento de cada mil no afecta el producto).

Revisando cómo lo resuelven los players del mercado:

- **Airbnb** — separa el fetch de datos (GraphQL persisted query) de la telemetría. Los eventos de comportamiento van a un endpoint dedicado (`tracking/jitney/logging/messages`), **batcheados y gzip-comprimidos**, fire-and-forget (responde 204, sin body). Cada card del feed carga un `loggingCorrelationId` que ata la impresión/click de vuelta a la búsqueda y al ranking que la produjo.
- **Habi** — REST plano sin telemetría de comportamiento expuesta; la card viene pre-calculada server-side, pero no hay pipeline de impresiones visible.

La pregunta: ¿cómo mandamos estos eventos desde el cliente sin bloquear la UI ni acoplar la captura al request del feed?

Aclaración de términos: **no es un webhook** (eso es server→server). Es lo opuesto — **client→server beacon**: el browser del usuario emite el evento y se olvida.

## Decisión

Pipeline de cuatro tramos, fire-and-forget de punta a punta:

1. **Captura en el cliente.** Click → handler directo. Impresión → **`IntersectionObserver`**: el evento `impressed` se dispara solo cuando el card está ≥50% visible por ≥1s (es "lo miró", no "estaba en el DOM").
2. **Envío sin bloquear.** **`navigator.sendBeacon()`** (o `fetch(..., { keepalive: true })`) — sobrevive al unload de la pestaña. Eventos **batcheados** en memoria, flush cada N eventos / N segundos / en `visibilitychange`. Opcionalmente comprimidos (gzip) como hace Jitney.
3. **Collector tonto.** Un endpoint que **valida el shape y dropea a Kafka**, nada más — devuelve 204 sin body. Cero lógica en el request path para que escale; toda la inteligencia vive downstream.
4. **Consumer en analytics-ms.** Topics `listing.impressed` / `listing.clicked` → consumer en analytics-ms que agrega y persiste, alimentando el recomendador / ranking del feed.

**Correlation ID**: cada card del feed carga un ID (+ su `position`), y el evento de impresión/click lo reenvía. Así analytics puede atribuir comportamiento a la búsqueda y el ranking exactos que lo generaron. Sin esto las impresiones son ruido sin contexto.

**Privacidad**: para el MVP, identificar por `session_id` anónimo sin PII — da la señal de comportamiento sin el problema legal de perfilar a la persona. El tracking end-to-end queda atado a consentimiento (analytics opt-in) antes de asociar a un `user_id`.

## Alternativas consideradas

- **POST síncrono normal por cada evento** — bloquea la UI, no sobrevive al unload (justo cuando el usuario clickea y navega se pierde el click), y un endpoint por evento no escala al volumen de impresiones. El beacon batcheado existe precisamente para este caso.
- **Disparar `impressed` al renderizar el card** — sobre-cuenta: cuenta cards fuera de viewport o que el usuario nunca vio. `IntersectionObserver` con umbral de visibilidad+tiempo es la señal honesta.
- **Procesar el evento en el request path del collector** (escribir a DB directo) — acopla la latencia del beacon a la DB y no absorbe picos. Kafka como buffer desacopla productor de consumidor.
- **Atar la captura al request del feed** (mandar impresiones como parte de la query de la siguiente página) — mezcla fetch de datos con telemetría, infla el payload del feed y pierde los eventos del último viewport si no hay siguiente página.

## Consecuencias

- ✅ La captura no bloquea ni puede romper la UI del feed: si el beacon falla, el usuario no se entera.
- ✅ Escala a alto volumen: el collector es O(validar+enqueue); los picos los absorbe Kafka.
- ✅ El correlation ID deja el contrato listo para atribuir comportamiento al ranking → habilita el recomendador de [[open-items]].
- ✅ Reusa la frontera async que ya existe en la arquitectura (Kafka properties↔analytics) en vez de inventar un canal nuevo.
- ❌ Eventual e inexacto por diseño: se pierden eventos (aceptable para impresiones, **no** para algo transaccional).
- ❌ Suma infra nueva: un endpoint collector, dos topics y un consumer en analytics-ms que hoy no existen.
- ❌ Trae carga de cumplimiento (consentimiento, anonimización) que hay que resolver antes de asociar eventos a usuarios identificados.

## Open items

- Decidir **dónde vive el collector**: ruta en properties-service vs. servicio de ingestión dedicado. El `workers/` de properties hoy está vacío y es candidato natural al consumer.
- Definir el **schema del evento** (`listing_id`, `correlation_id`, `position`, `session_id`, `event_type`, `ts`, `dwell_ms`).
- Resolver consentimiento/anonimización antes de cruzar de `session_id` a `user_id`.
- Atar con el correlation ID que hoy **no** emite `PropertyCardSchema` — habría que agregarlo al feed primero.

## Claims

- No existe endpoint collector de impresiones ni topics `listing.impressed`/`listing.clicked`; el ítem está registrado como pendiente en [[open-items]] ([open-items.md](../open-items.md)).
- El directorio `workers/` de properties-service solo contiene `__init__.py` — no hay consumer Kafka todavía ([workers/](backend/properties-service/src/app/workers)).
- analytics-service es el consumer designado para la señal de comportamiento, en línea con la frontera async properties↔analytics marcada "en definición" en la arquitectura ([architecture.md](../architecture.md)).
- `PropertyCardSchema` no incluye hoy un correlation/logging ID por resultado ([property_card.py](backend/properties-service/src/app/services/shared/schemas/property_card.py)).
