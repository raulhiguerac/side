---
title: ADR-0006 — Isócronas con ORS + H3 para reachable POIs
status: draft
last-verified: 2026-06-10
owners: [catalog-service, frontend]
related:
  - "[[catalog-service-poi-lifecycle]]"
  - "[[catalog-service-architecture]]"
  - "[[adr-postgis-h3-hybrid]]"
  - "[[adr-poi-cache-aside]]"
  - "[[frontend-map-component]]"
  - "[[open-items]]"
decision-date: 2026-06-10
decision-status: accepted
---

# ADR-0006 — Isócronas con ORS + H3 para reachable POIs

## Contexto

La vista de detalle de propiedad necesita responder la pregunta del usuario: **¿qué tan lejos estoy, caminando o en carro, de lugares relevantes?** Los POIs estáticos (distancia en línea recta) son un proxy débil — una propiedad puede tener un colegio a 300 m en línea recta pero a 20 min caminando por topografía o infraestructura vial.

El diferenciador real es la **isocrona**: dado un punto de origen y un tiempo T en modo M (walking, driving, cycling), calcular el polígono de área alcanzable y mostrar los POIs que caen dentro.

Decisiones involucradas:
1. Qué motor de routing usar.
2. Cómo indexar espacialmente el polígono resultado.
3. Cómo cachear para no re-calcular en cada request.
4. Dónde vive la responsabilidad (qué servicio, qué endpoint).
5. Cómo manejar el edge case de celdas H3 en el borde del polígono.
6. Cómo renderizar en el frontend.
7. Cómo unificar el tag set de POIs entre Overpass y el AVM.
8. Cómo pre-seedear Bogotá para eliminar el cold start.

## Decisión

### 1. Motor de routing: OpenRouteService (ORS)

**ORS self-hosted o tier gratis**, no Mapbox Isochrones API.

Mapbox fue descartado por cobertura insuficiente en Colombia — la red vial colombiana tiene gaps significativos en el grafo de routing de Mapbox, especialmente en zonas periféricas de Bogotá. ORS usa datos de OpenStreetMap, que tienen mejor cobertura local y son actualizables.

Alternativas descartadas:
- **Mapbox Isochrones API** — cobertura deficiente en Colombia, vendor lock-in, costo por request.
- **Valhalla** — más potente pero operativamente más pesado; ORS alcanza para el caso de uso actual.
- **OSRM** — solo routing punto-a-punto, no genera polígonos de isocrona nativamente.

### 2. Indexación espacial del polígono: H3

El polígono de isocrona (GeoJSON) se convierte a un conjunto de celdas H3 con `h3.polygon_to_cells(polygon, res=9, contain="center")`.

`contain="center"` significa que solo se incluye una celda si su centroide cae dentro del polígono — evita incluir celdas que solo rozan el borde. Esto introduce un error de hasta ~150 m en el borde (mitad de celda r9), aceptable para el caso de uso.

Las celdas resultantes se usan para hacer lookup de POIs: `SELECT * FROM poi WHERE h3_index = ANY(:cells)` — el índice sobre `poi.h3_index` lo hace eficiente.

### 3. Caching por property_id

**Cache key**: `geo:iso:{property_id}:{minutes}:{mode}` — TTL 24 h.

El origen de la isocrona siempre es el punto fijo de la propiedad, por lo que `property_id` es un identificador natural y estable. Esto hace la key determinista, barata de construir y fácil de invalidar si la ubicación de la propiedad cambia.

El response completo (polígono + POIs) se cachea como una unidad en Redis. Ventajas:
- Segunda visita al mismo listing con mismo modo/minutos → hit de Redis, ORS no se toca.
- No hay que coordinar dos caches independientes — el polígono y los POIs son inseparables.
- El polígono GeoJSON es pequeño (~5–20 KB) — costo de almacenamiento en Redis despreciable.

Miss → llama ORS → convierte a H3 → query POIs → cachea response completo → devuelve.

### 4. Responsabilidad: catalog-service — response unificado

**Nuevo UC en el dominio `geo_resolution`**: `ReachablePoiUseCase`.

Endpoint: `GET /v1/geo-resolution/reachable-pois?property_id=&minutes=&mode=`

El UC resuelve internamente las coordenadas desde `property_id` y devuelve **un único response con polígono + POIs**:

```json
{
  "polygon": { "type": "Feature", "geometry": { ...GeoJSON Polygon... } },
  "pois": [
    { "name": "Colegio Los Nogales", "category": "education", "lat": ..., "lon": ... }
  ]
}
```

El frontend no necesita dos requests ni coordinar estado — recibe todo en uno. El polígono ya está calculado cuando se buscan los POIs; devolverlo no tiene costo adicional.

Modos soportados: `walking` (default), `driving-car`, `cycling-regular`.

### 5. Edge case de borde

`contain="center"` es la estrategia de contención elegida (no intersección parcial). Razones:
- Intersección parcial infla el área percibida — un POI a 25 min aparece como accesible en 15 min.
- "Center" es conservador y honesto con el usuario.
- El error introducido (~150 m) es tolerable frente a la imprecisión inherente del routing en ciudad.

### 6. Render en frontend

El polígono del response se renderiza como capa translúcida en Leaflet con `L.geoJSON()` (`fillOpacity: 0.15`, `color: brand-primary`). La lista de POIs se muestra en el panel lateral de la vista de detalle.

El usuario puede cambiar modo y minutos con controles simples; cada cambio dispara un nuevo request. El segundo request al mismo `property_id + mode + minutes` es un hit de Redis — respuesta instantánea.

### 7. Unificación del tag set Overpass ↔ AVM

El tag set actual de `overpass.py` (14 amenity + 4 leisure + 3 shop) es un subconjunto pequeño del que usa el AVM en training (5 keys OSM, 15 categorías, 70+ valores). Esto significa que Overpass fetchea POIs que el AVM no conoce, y el AVM entrenó con categorías que Overpass no captura (transport via `public_transport`, health via `healthcare`, fashion, home, electronics, etc.).

**Decisión**: actualizar `overpass.py` para incluir los 5 keys OSM (`amenity`, `shop`, `public_transport`, `leisure`, `healthcare`) con el tag set completo del notebook. Actualizar `_extract_category` en `poi_provider.py` para aplicar el mismo mapping invertido de 15 categorías. Así la columna `category` en `points_of_interest` queda alineada con lo que espera el AVM — el modelo puede migrar a consumir esta tabla via ETL sin inconsistencias.

### 8. Init container — seed PBF de Colombia

Overpass fire-and-forget resuelve el cold start por zona a medida que llegan requests, pero para la isocrona Bogotá necesita estar pre-seedeada — el primer request a cualquier propiedad no puede esperar un fetch de Overpass en tiempo real.

**Decisión**: init container que corre `osmium` sobre el PBF de Colombia (disponible en Geofabrik, ~150 MB) y hace bulk insert en `points_of_interest` con `source=seed`. Usa el mismo mapping de 15 categorías. El fire-and-forget de Overpass sigue operando para refreshes (`is_stale=True`) y zonas fuera de Bogotá. El seed no reemplaza Overpass — lo complementa.

El patrón osmium ya está validado en el notebook `02_feature_engineering.ipynb` (`PoiHandler` sobre `colombia-260510.osm.pbf`).

## Consecuencias

- ✅ Tag set unificado Overpass ↔ AVM — `points_of_interest.category` consistente con las 15 categorías del modelo, listo para ETL.
- ✅ Init container PBF elimina cold start — Bogotá pre-seedeada antes del primer request.
- ✅ Diferenciador real vs FincaRaíz/Metrocuadrado/Cerouno — ninguno tiene isócronas en Colombia.
- ✅ Reutiliza H3 y el índice `poi.h3_index` ya existente — sin nueva infraestructura de datos.
- ✅ Cache por `property_id + mode + minutes` — key determinista, response unificado, ORS no se re-ejecuta en visitas repetidas.
- ✅ Caller agnóstico al motor de routing — cambiar ORS por otra cosa no afecta el contrato.
- ❌ ORS requiere deploy propio para producción (tier gratis tiene rate limits). Self-hosted en k3s es el plan.
- ❌ El polígono de isocrona en zonas con mala cobertura OSM puede ser impreciso — en Colombia este es un riesgo real en zonas periféricas.
- ❌ Cold start por zona: si los POIs de las celdas del polígono no fueron fetcheados aún, el primer request dispara el fetch de Overpass además del cálculo de ORS. Mitigación: el fetch de POIs es un side-effect background async (ya implementado en [[catalog-service-poi-lifecycle]]).

## Claims

- El endpoint `GET /v1/geo-resolution/reachable-pois` no existe aún — es el objetivo de implementación de este ADR.
- `h3.polygon_to_cells(polygon, res=9, contain="center")` es la función de conversión — `contain="center"` excluye celdas cuyo centroide queda fuera del polígono.
- La cache key es `geo:iso:{property_id}:{minutes}:{mode}` — el response completo (polígono + POIs) se cachea como unidad, TTL 24 h.
- ORS fue elegido sobre Mapbox por cobertura en Colombia — Mapbox tiene gaps en la red vial colombiana.
- La responsabilidad del UC vive completamente en catalog-service; properties-service y el frontend son callers sin lógica de routing.
