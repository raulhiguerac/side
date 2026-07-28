---
title: H3 precompute on geometry enrich + bulk coordinate resolution
captured-from: conversation
captured-on: 2026-07-18
participants: [raul, claude]
---

## Context
Catalog-service was switching from purely on-demand H3 cell population (side-effect of `ResolvePoiUseCase`) to precomputing `h3_cells` when a neighborhood's geometry is enriched. This surfaced a question about whether the existing "cold cell" fallback query was still needed, and led to building a batch coordinate-resolution use case (for bulk async processing, e.g. resolving many properties at once) plus a real bug fix in H3 cell bookkeeping.

## Key conclusions
- `bulk_enrich_neighborhood_geometries` and the singular `enrich_neighborhood_geometry` UC now both precompute full `h3_cells` coverage via `h3_cells_for_geojson(geometry, resolution=settings.H3_RESOLUTION)` at the same time `geom` is set, instead of relying only on incremental on-demand population.
- The "cold cell" fallback (full sweep over `Neighborhood.geom` without the `h3_cells` prefilter) in `get_location_by_point`/`get_location_by_points` must stay, for two reasons: (1) `CreateNeighborhoodUseCase`/`UpdateNeighborhoodUseCase` never touch `geom`/`h3_cells` at all — only the enrich flows do — so coverage is inconsistent across neighborhoods; (2) H3 polyfill (`h3.geo_to_cells`) decides cell membership by cell-center containment, so points near a neighborhood's border can land in a cell whose center falls just outside the polygon and thus isn't in the precomputed array, even for fully-precomputed neighborhoods.
- Added `get_location_by_points` (adapter + port) using `unnest(...)` + `LATERAL JOIN` to resolve a whole batch of points in one/two SQL round trips instead of N — mirrors the existing single-point `get_location_by_point` fallback pattern (H3 prefilter pass, then a second pass only for misses).
- New use case `BulkResolveLocationsByCoordinatesUseCase` (`geo_resolution/use_cases/bulk_resolve_locations_by_coordinates.py`): takes `list[PointToResolveBase]`, computes each point's H3 cell in a threadpool (`_enrich_with_cells`), calls the adapter, wraps DB errors with log + re-raise.
- Schema split for clarity: `PointToResolveBase` (id, lat, lon) is the caller-facing input; `PointToResolve` extends it with the computed `cell` for internal SQL matching; `ResolvedPoint` (id, location) replaces the old `list[tuple[str, Optional[LocationByCoordinates]]]` return shape.
- Wired DI (`api/deps/geo_resolution.py`: `bulk_resolve_locations_by_coordinates_uc`) and a new endpoint `POST /geo-resolution/by-coordinates/bulk` (body: `BulkResolveLocationsRequest`, response: `list[ResolvedPoint]`).
- Found and fixed a real bug in `update_neighborhood_h3_cells`: it used `func.array_append(Neighborhood.h3_cells, h3_index)` unconditionally. Every time a cell goes through the stale→refetch cycle in `ResolvePoiUseCase._fetch_and_persist`, the same `h3_index` gets appended again, so `h3_cells` accumulates duplicates indefinitely for recurrently-fetched cells (bloats row/GIN index size, doesn't break correctness). Fixed purely at the SQL layer with a conditional append (`CASE WHEN h3_cells @> ARRAY[h3_index] ... THEN h3_cells ELSE array_append(...)`), with zero changes to `resolve_poi.py`'s calling logic.

## Open questions
- Whether the bulk endpoint should also fire `ResolvePoiUseCase` background tasks per resolved point (like the singular `/by-coordinates` endpoint does) — attempted once with a per-cell dedup guard, then explicitly reverted; not implemented for now.
- No batch-size chunking on `get_location_by_points` — very large batches embed literal arrays in the `unnest` query, which may need chunking. Deferred to the (properties-service) caller, not solved in catalog-service.
- Whether existing production data already has duplicate entries in `h3_cells` from before this fix (would need a separate backfill/dedup pass, not just the forward-fix).

## Next steps
- properties-service: build the bulk-resolve caller UC that uses `POST /geo-resolution/by-coordinates/bulk` to assign `neighborhood_id`/`locality_id`/`country_id` to a batch of properties without N round trips.
- users-service: an analogous batch-resolution need was flagged (resolving user IDs in bulk) — not started, explicitly parked.
