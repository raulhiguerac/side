---
title: "ADR-0014 — El feed en mapa pinta todo el bbox con cluster y la lista hace scroll infinito"
status: stable
last-verified: 2026-10-09
owners: [frontend]
related:
  - "[[frontend-map-component]]"
  - "[[frontend-architecture]]"
  - "[[properties-service-search]]"
sources: [../../../sources/frontend/2026-10-09-api-layer-map-cluster-and-typecheck.md]
decision-date: 2026-10-09
decision-status: accepted
---

# ADR-0014 — El feed en mapa pinta todo el bbox con cluster y la lista hace scroll infinito

## Contexto

`GET /v1/search/feed/map` devuelve **todas** las propiedades del bbox, sin orden: primero las celdas H3 cacheadas y después las nuevas. El front las barajaba con `sort(() => Math.random() - 0.5)` y pintaba en el mapa **solo la página actual** (20 o 40). La paginación estaba ahí porque con muchas propiedades los iconos se superponían.

El resultado: zonas del mapa vacías aunque hubiera oferta, una muestra distinta en cada movimiento y un barajado sesgado (un comparador aleatorio no es uniforme y rompe el contrato de `sort`). Las propiedades promocionadas tampoco tenían prioridad.

## Decisión

**El mapa pinta todo el bbox y un cluster evita que los iconos se superpongan. La lista pagina por su cuenta, con scroll infinito y orden determinista.**

- **Mapa:** `markers` sale de `allItems`. `useMarkerCluster` agrupa los cercanos en burbujas con el conteo, que se separan al acercar. Con el zoom máximo los abre en abanico (`spiderfyOnMaxZoom`, que markercluster trae activo por defecto). Ver [[frontend-map-component]].
- **Lista:** `items` son los primeros `visibleCount` de `allItems`, en tandas de 20. Un centinela con `IntersectionObserver` (`useInfiniteScroll`) carga la siguiente tanda. **No hace requests**: los datos ya están.
- **Orden:** `sortForMap` pone primero las promocionadas, luego ordena por distancia al centro del bbox y desempata por `id`. Al mover el mapa el orden cambia de forma predecible, y eso reparte la exposición sin azar.
- **Respuestas:** solo se aplica la del último bbox pedido (`latestRequest`).

## Alternativas consideradas

- **Marcadores de la página actual** (lo que había). Evita la superposición, pero deja huecos y el mapa no muestra la densidad real.
- **Muestreo repartido por cuadrícula.** Cada página toma una propiedad por celda de una cuadrícula de, por ejemplo, 6×6. Es barato y elimina los huecos, pero el mapa sigue mostrando solo 20–40 propiedades.
- **Ordenar en el backend** (`ORDER BY` en `get_by_bbox` y fusión de la caché por celda respetando ese orden). Es lo más correcto a largo plazo, pero toca el backend y la caché. Queda abierto.

## Consecuencias

- El mapa muestra la oferta real del área; la lista y el mapa salen de la misma fuente (`_allItems` en `useFeedMap`).
- Con cientos de propiedades, el cluster actualiza por diferencias y los iconos se renderizan una vez por tipo y estado, así que el costo no crece con cada movimiento.
- Al pasar el ratón por un marcador cuya tarjeta todavía no está pintada en la lista no pasa nada (decisión consciente: no saltar ni cargar mientras se mueve el ratón).
- Se pierde el barajado. Si se quiere rotar la exposición entre propiedades equivalentes, habría que hacerlo de forma determinista (semilla por sesión), no con `Math.random`.

## Claims

- `MapView` construye `markers` a partir de `allItems` y la lista a partir de `items` de `useFeedMap` ([views/properties/feed/MapView.vue](frontend/src/views/properties/feed/MapView.vue)).
- `useFeedMap` ordena con `sortForMap` y no usa `Math.random` ([composables/feed/useFeedMap.ts:31](frontend/src/composables/feed/useFeedMap.ts#L31)).
- `sortForMap` ordena por `is_promoted`, luego por distancia al centro del bbox y luego por `id` ([utils/feedMap.ts](frontend/src/utils/feedMap.ts)).
- `loadMore` suma `PAGE_SIZE.FEED_MAP_CHUNK` a `visibleCount` sin hacer requests ([composables/feed/useFeedMap.ts:39-41](frontend/src/composables/feed/useFeedMap.ts#L39-L41)).
