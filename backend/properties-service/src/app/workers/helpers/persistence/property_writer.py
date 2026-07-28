import logging
import time
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.workers.schemas.bulk_schemas import BulkRowError

logger = logging.getLogger(__name__)


def collapse_duplicate_ids(built_rows: list[dict]) -> list[dict]:
    """Collapses rows that derive the same property id, keeping the last one.

    Postgres rejects an INSERT whose ON CONFLICT target row appears more than
    once ("cannot affect row a second time"), so a chunk carrying two rows with
    the same id fails as a whole and falls back to row-by-row — correct, but
    orders of magnitude slower. Since ids come from the CSV's external_id, a file
    that repeats one inside a single chunk hits this every time.

    Last occurrence wins, which is what would happen anyway if the duplicates had
    landed in different chunks: the later upsert overwrites the earlier.
    """
    by_id: dict = {}
    for row in built_rows:
        prop, _, _ = row["value"]
        by_id[prop.id] = row
    return list(by_id.values())


async def persist_chunk(
        built_rows: list[dict],
        *,
        uow: AdminUnitOfWork,
    ) -> tuple[int, list[BulkRowError]]:
    """Bulk-inserts the chunk, falling back to row-by-row so one bad row doesn't
    cost the whole chunk. Each retry runs inside its own savepoint, released on
    success so savepoints don't nest across the loop."""
    started = time.monotonic()

    deduped = collapse_duplicate_ids(built_rows)
    collapsed = len(built_rows) - len(deduped)
    if collapsed:
        logger.info(
            "collapsed rows sharing a derived id",
            extra={"collapsed": collapsed, "writing": len(deduped)},
        )

    try:
        await run_in_threadpool(
            partial(
                uow.properties.bulk_insert,
                properties = [row["value"] for row in deduped],
            )
        )
        await uow.commit()
        logger.info(
            "bulk_insert committed",
            extra={"inserted": len(deduped), "elapsed_s": round(time.monotonic() - started, 2)},
        )
        return len(deduped), []
    except Exception as exc:
        await uow.rollback()
        logger.warning(
            "bulk_insert failed, falling back to row-by-row",
            extra={"total": len(deduped)},
            exc_info=exc,
        )

    errors: list[BulkRowError] = []
    ok_count = 0

    for row in deduped:
        prop, _, _ = row["value"]
        try:
            await uow.begin_nested()
            await run_in_threadpool(partial(uow.properties.add, property=row["value"]))
            await uow.release_savepoint()
            ok_count += 1
        except Exception as exc:
            await uow.rollback_to_savepoint()
            logger.warning(
                "failed to insert property",
                extra={"property_id": str(prop.id), "line": row["line"]},
                exc_info=exc,
            )
            errors.append(
                BulkRowError(line=row["line"], ref=row["ref"], issues=[str(exc)])
            )

    if ok_count:
        await uow.commit()

    logger.warning(
        "row-by-row fallback done",
        extra={
            "inserted": ok_count,
            "failed": len(errors),
            "elapsed_s": round(time.monotonic() - started, 2),
        },
    )

    return ok_count, errors
