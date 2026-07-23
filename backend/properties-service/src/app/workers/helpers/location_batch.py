from app.services.admin.schemas.admin_schemas import BulkRowError
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.schemas.catalog_schemas import PointToResolve
from app.workers.helpers.row_ref import row_ref


async def process_location_batch(
        batch: list[dict],
        *,
        catalog: CatalogGateway,
    ) -> tuple[list[dict], list[BulkRowError]]:
    """Resolves lat/lon for a batch in one call to catalog and merges the
    result back into each row, correlated by a per-row uuid."""
    errors: list[BulkRowError] = []
    points: list[PointToResolve] = []
    rows_by_id: dict[str, dict] = {}

    for row in batch:
        try:
            points.append(
                PointToResolve(id=row['id'], lat=row["value"].lat, lon=row["value"].lon)
            )
            rows_by_id[row['id']] = row
        except (KeyError, ValueError) as exc:
            errors.append(
                BulkRowError(
                    line = row["line"],
                    ref = row_ref(row["value"].model_dump()),
                    issues = [f"invalid lat/lon: {exc}"],
                )
            )

    resolved = await catalog.get_locations_bulk(points=points)

    enriched: list[dict] = []
    for result in resolved:
        row = rows_by_id[result.id]
        if result.location is None:
            errors.append(
                BulkRowError(
                    line = row["line"],
                    ref = row_ref(row["value"].model_dump()),
                    issues = ["location not resolved for given coordinates"],
                )
            )
            continue

        row.update(result.location.model_dump())
        enriched.append(row)

    return enriched, errors
