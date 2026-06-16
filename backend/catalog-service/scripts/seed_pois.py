#!/usr/bin/env python3
"""
Seed POIs from an OSM PBF file into the catalog DB.

Usage:
    uv run python scripts/seed_pois.py --pbf <path.pbf> --locality-id <uuid>

Dependencies (add to pyproject.toml):
    osmium   — pyosmium Python bindings
    h3       — already present
    psycopg2-binary — already present

Environment variables:
    DATABASE_CATALOG_URL  — postgres DSN (same as catalog-service)
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from itertools import islice

import h3
import osmium
import psycopg2
import psycopg2.extras

POI_TAGS = ("amenity", "shop", "leisure", "healthcare", "public_transport", "tourism", "office")
BATCH_SIZE = 500

OSM_TYPE_PREFIX = {
    "n": "node",
    "w": "way",
    "r": "relation",
}

UPSERT_SQL = """
INSERT INTO points_of_interest (
    id, locality_id, neighborhood_id,
    external_id, source, raw_response, fetched_at, is_stale,
    name, search_name, full_address, category, subcategories,
    latitude, longitude, h3_index, geom,
    phone, website, is_active,
    created_at, updated_at
)
VALUES %s
ON CONFLICT (external_id, source) DO UPDATE SET
    name         = EXCLUDED.name,
    search_name  = EXCLUDED.search_name,
    category     = EXCLUDED.category,
    raw_response = EXCLUDED.raw_response,
    fetched_at   = EXCLUDED.fetched_at,
    is_stale     = false,
    updated_at   = EXCLUDED.updated_at
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed POIs from OSM PBF")
    parser.add_argument("--pbf", required=True, help="Path to .osm.pbf file")
    parser.add_argument("--locality-id", required=True, help="UUID of the target locality")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
    return parser.parse_args()


def pick_category(tags: dict) -> str | None:
    for tag in POI_TAGS:
        if val := tags.get(tag):
            return val
    return None


def build_raw_response(osm_id: int, lat: float, lon: float, tags: dict) -> str:
    return json.dumps({
        "type": "node",
        "id": osm_id,
        "lat": lat,
        "lon": lon,
        "tags": tags,
    })


def batched(iterable, n):
    it = iter(iterable)
    while chunk := list(islice(it, n)):
        yield chunk


class PoiHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.features: list[dict] = []

    def node(self, n):
        if not n.location.valid():
            return
        tags = {k: v for k, v in n.tags}
        if not any(t in tags for t in POI_TAGS):
            return
        self.features.append({
            "id": n.id,
            "lat": float(n.location.lat),
            "lon": float(n.location.lon),
            "tags": tags,
        })


def build_row(feat: dict, locality_id: uuid.UUID, now: datetime) -> tuple:
    osm_id = feat["id"]
    lat, lon = feat["lat"], feat["lon"]
    tags = feat["tags"]

    name = tags.get("name") or pick_category(tags) or f"node/{osm_id}"
    category = pick_category(tags)
    external_id = f"node/{osm_id}"
    h3_index = h3.latlng_to_cell(lat, lon, 9)
    raw = build_raw_response(osm_id, lat, lon, tags)
    geom_wkt = f"SRID=4326;POINT({lon} {lat})"

    return (
        str(uuid.uuid4()),   # id
        str(locality_id),    # locality_id
        None,                # neighborhood_id
        external_id,         # external_id
        "seed",              # source
        raw,                 # raw_response
        now,                 # fetched_at
        False,               # is_stale
        name,                # name
        name.lower(),        # search_name
        None,                # full_address
        category,            # category
        None,                # subcategories
        lat,                 # latitude
        lon,                 # longitude
        h3_index,            # h3_index
        geom_wkt,            # geom
        None,                # phone
        None,                # website
        True,                # is_active
        now,                 # created_at
        now,                 # updated_at
    )


def main() -> None:
    args = parse_args()

    db_url = os.environ.get("DATABASE_CATALOG_URL")
    if not db_url and not args.dry_run:
        print("ERROR: DATABASE_CATALOG_URL not set", file=sys.stderr)
        sys.exit(1)

    locality_id = uuid.UUID(args.locality_id)
    now = datetime.now(timezone.utc)

    print(f"Parsing {args.pbf}...")
    handler = PoiHandler()
    handler.apply_file(args.pbf)
    print(f"Found {len(handler.features)} POI nodes.")

    conn = psycopg2.connect(db_url) if not args.dry_run else None

    total = 0
    skipped = 0

    try:
        for batch in batched(handler.features, args.batch_size):
            rows = []
            for feat in batch:
                try:
                    rows.append(build_row(feat, locality_id, now))
                except Exception as exc:
                    print(f"WARN skip node/{feat['id']}: {exc}", file=sys.stderr)
                    skipped += 1
                    continue

            if args.dry_run:
                total += len(rows)
                print(f"[dry-run] batch {len(rows)} rows (total so far: {total})")
                continue

            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    UPSERT_SQL,
                    rows,
                    template="(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,ST_GeomFromEWKT(%s),%s,%s,%s,%s,%s)",
                    page_size=args.batch_size,
                )
            conn.commit()
            total += len(rows)
            print(f"Upserted {total} POIs (skipped {skipped})...", end="\r")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        if conn:
            conn.close()

    print(f"\nDone. Total upserted: {total} | Skipped: {skipped}")


if __name__ == "__main__":
    main()
