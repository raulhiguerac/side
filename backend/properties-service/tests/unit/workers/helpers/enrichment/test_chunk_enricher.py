import uuid
from unittest.mock import AsyncMock, patch

from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.enrichment.chunk_enricher import enrich_chunk
from app.workers.schemas.bulk_schemas import BulkPropertyCsvRow

ACCOUNT_A = ResolvedAccount(account_id=uuid.uuid4(), email="a@test.com")
ACCOUNT_B = ResolvedAccount(account_id=uuid.uuid4(), email="b@test.com")


def _row(email: str, line: int = 2) -> dict:
    value = BulkPropertyCsvRow(
        external_id=f"CSV-{line}",
        area_m2="80",
        cuartos="3",
        estrato="4",
        tipo="venta",
        parqueaderos="1",
        banios="2",
        piso="3",
        precio="350000000",
        precio_admin="0",
        tipo_propiedad="apartamento",
        lat=4.65,
        lon=-74.05,
        antiguedad="1 a 8 años",
        email=email,
    )
    return {"line": line, "id": str(uuid.uuid4()), "value": value}


def _patch_geo(rows_out=None, errors_out=None):
    return patch(
        "app.workers.helpers.enrichment.chunk_enricher.process_location_batch",
        new_callable=AsyncMock,
        return_value=(rows_out if rows_out is not None else [], errors_out or []),
    )


# ---------------------------------------------------------------------------
# email_cache — the whole point is to not pay twice for the same owner
# ---------------------------------------------------------------------------

async def test_resolves_only_emails_missing_from_cache():
    resolve = AsyncMock(return_value=[ACCOUNT_B])
    cache = {ACCOUNT_A.email: ACCOUNT_A}
    rows = [_row(ACCOUNT_A.email), _row(ACCOUNT_B.email)]

    with _patch_geo(rows_out=rows):
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=resolve, email_cache=cache)

    resolve.assert_awaited_once_with({ACCOUNT_B.email})
    assert cache == {ACCOUNT_A.email: ACCOUNT_A, ACCOUNT_B.email: ACCOUNT_B}


async def test_skips_the_users_call_when_every_email_is_cached():
    resolve = AsyncMock()
    cache = {ACCOUNT_A.email: ACCOUNT_A}
    rows = [_row(ACCOUNT_A.email), _row(ACCOUNT_A.email)]

    with _patch_geo(rows_out=rows):
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=resolve, email_cache=cache)

    resolve.assert_not_awaited()


async def test_deduplicates_repeated_emails_within_one_chunk():
    resolve = AsyncMock(return_value=[ACCOUNT_A])
    rows = [_row(ACCOUNT_A.email) for _ in range(5)]

    with _patch_geo(rows_out=rows):
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=resolve, email_cache={})

    resolve.assert_awaited_once_with({ACCOUNT_A.email})


async def test_cache_persists_so_a_later_chunk_costs_nothing():
    resolve = AsyncMock(return_value=[ACCOUNT_A])
    cache: dict = {}
    rows = [_row(ACCOUNT_A.email)]

    with _patch_geo(rows_out=rows):
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=resolve, email_cache=cache)
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=resolve, email_cache=cache)

    assert resolve.await_count == 1


# ---------------------------------------------------------------------------
# Geo results and errors pass straight through
# ---------------------------------------------------------------------------

async def test_returns_geo_rows_and_errors_untouched():
    rows = [_row(ACCOUNT_A.email)]
    sentinel_errors = ["boom"]

    with _patch_geo(rows_out=rows, errors_out=sentinel_errors):
        enriched, errors = await enrich_chunk(
            rows, catalog=AsyncMock(), resolve_emails=AsyncMock(return_value=[ACCOUNT_A]), email_cache={}
        )

    assert enriched == rows
    assert errors == sentinel_errors


async def test_geo_still_runs_when_there_are_no_new_emails():
    rows = [_row(ACCOUNT_A.email)]
    cache = {ACCOUNT_A.email: ACCOUNT_A}

    with _patch_geo(rows_out=rows) as geo:
        await enrich_chunk(rows, catalog=AsyncMock(), resolve_emails=AsyncMock(), email_cache=cache)

    geo.assert_awaited_once()
