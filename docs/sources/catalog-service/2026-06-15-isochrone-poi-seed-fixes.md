---
title: Isochrone schema fix, ORS settings, and PBF seed script
captured-from: conversation
captured-on: 2026-06-15
participants: [raul, claude]
---

## Context
`ResolveIsochroneUseCase` had a crash risk and hardcoded config. The isochrone response returned a raw nested array with no schema. POI seeding relied only on Overpass at runtime with no bulk seed path.

## Key conclusions
- `GeoJsonPolygon` schema added to `services/geo_resolution/schemas/isochrone.py`: `{ type: "Polygon", coordinates: number[][][] }`. The `IsochroneEntry.isochrone` and `ReachablePoisResult.isochrone` fields now use this instead of `list[list[list[float]]]`.
- `resolve_isochrone.py` crash fix: changed `entry.isochrone[0]` → `entry.isochrone.coordinates[0]` with guard `if entry.range and entry.isochrone`.
- ORS config moved to `settings.py`: `ORS_URL: str = os.getenv("ORS_URL", "")` and `ORS_TIMEOUT_SECONDS: float = 5.0`. `routing.py` now imports settings instead of calling `os.getenv` directly.
- `scripts/seed_pois.py` created. Uses `pyosmium.SimpleHandler` to parse a `.pbf` file, filters nodes by POI tags (`amenity`, `shop`, `leisure`, `healthcare`, `public_transport`, `tourism`, `office`), computes `h3_index` at resolution 9, bulk upserts with `psycopg2 execute_values` + `ON CONFLICT (external_id, source) DO UPDATE`. External ID format: `node/{osm_id}` (matches Overpass). Supports `--dry-run`, `--locality-id`, `--pbf`, `--batch-size`.
- `osmium>=3.7.0` added to `pyproject.toml`.

## Open questions
- The `PoiProviderGateway` protocol still declares `get_isochrones` as sync — needs updating to match the async adapter.

## Next steps
- Run seed script as init container on deploy for Bogotá PBF.
- Fix port protocol sync/async mismatch.
