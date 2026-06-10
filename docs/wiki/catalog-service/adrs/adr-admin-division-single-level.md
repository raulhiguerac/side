---
title: ADR-0002 — AdminDivision de un solo nivel (sin recursión)
status: stable
last-verified: 2026-05-21
owners: [catalog-service]
related:
  - "[[catalog-service]]"
  - "[[catalog-service-catalog-admin]]"
sources: [../../../sources/catalog-service/2026-05-21-foundational-qa.md]
decision-date: 2026-05-21
decision-status: accepted
---

# ADR-0002 — AdminDivision de un solo nivel (sin recursión)

## Contexto

La jerarquía administrativa real de los países es heterogénea:
- **Colombia**: Departamento → Municipio → (Comuna/Localidad) → Barrio
- **España**: Comunidad Autónoma → Provincia → Municipio → Barrio
- **Brasil**: Estado → Mesorregião → Microrregião → Município
- **USA**: State → County → City → Neighborhood
- **México**: Estado → Municipio → Colonia

Un modelo "fiel" requeriría una tabla `AdminDivision` con FK a sí misma (`parent_id`), permitiendo recursión arbitraria. Eso complica las queries (recursive CTEs), las migrations, los seeds y la UX del frontend (cuántos niveles muestro en el autocomplete).

## Decisión

Modelo simplificado de 4 niveles fijos sin recursión:

```
Country  →  AdminDivision (1 nivel)  →  Locality  →  Neighborhood
```

- `AdminDivision` es **el nivel inmediatamente debajo del país** (Departamento, State, Comunidad Autónoma, Estado).
- `Locality` es el **lugar poblado** (municipio/ciudad/pueblo/villa). Su tipo está en el enum `LocalityType` (city/town/village).
- `Neighborhood` es el **barrio** dentro de la locality (opcional para localities pequeñas).
- Niveles intermedios (provincia, mesorregión, comuna) **se pierden** del modelo.

## Alternativas consideradas

- **Adjacency list recursiva** (`AdminDivision.parent_id` self-FK) — flexible pero requiere CTEs recursivas, JSON paths en autocomplete, y más complejidad de seed.
- **Materialized path / nested set** — buenos para reads jerárquicos pero costosos de mantener en writes.
- **Modelo per-país** (tablas distintas según jurisdicción) — máxima fidelidad, máximo costo de mantenimiento.
- **Sin AdminDivision** (Country → Locality directo) — más simple aún, pero pierde filtrado por depto que el frontend necesita para Colombia.

## Consecuencias

- ✅ Esquema simple, autocomplete del frontend trivial (3 selects encadenados).
- ✅ Seed de Colombia es directo: lista de departamentos + lista de municipios + barrios IDECA.
- ✅ Queries planas, sin CTEs ni gymnastic SQL.
- ✅ Frontend de admin de catálogo es manejable (no necesita tree component).
- ❌ Pierde provincia (España, Brasil) y casos mixtos — para esos países habrá que decidir cuál nivel mapeamos a `AdminDivision` (probablemente "el más relevante para el usuario final" — provincia en España, estado en Brasil).
- ❌ Si el producto escala a un país con jerarquía muy distinta (ej. India: State → Division → District → Subdivision → Block), tocará reabrir esta decisión.
- ❌ `Comuna` de Colombia (nivel intermedio Bogotá → Localidad → Barrio) no entra — la app trata "Bogotá" como Locality y los barrios IDECA debajo, saltando "Localidad" administrativa.

## Claims

- `AdminDivision` tiene una sola FK upstream (`country_id`), sin `parent_id` ([models/location.py:110-161](backend/catalog-service/src/app/models/location.py#L110-L161)).
- `Locality.admin_division_id` apunta directo a `AdminDivision`; no hay tabla intermedia ([models/location.py:201-207](backend/catalog-service/src/app/models/location.py#L201-L207)).
- El docstring del modelo declara explícitamente "Sin recursión. Un solo nivel." ([models/location.py:120](backend/catalog-service/src/app/models/location.py#L120)).
- `LocalityType` tiene 3 valores: `city`, `town`, `village` ([models/location.py:169-174](backend/catalog-service/src/app/models/location.py#L169-L174)).
