import logging
from functools import partial

from fastapi.concurrency import run_in_threadpool

from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.workers.schemas.bulk_schemas import BulkRowError

logger = logging.getLogger(__name__)


async def persist_chunk(
        built_rows: list[dict],
        *,
        uow: AdminUnitOfWork,
    ) -> tuple[int, list[BulkRowError]]:
    """Bulk-inserts the chunk, falling back to row-by-row so one bad row doesn't
    cost the whole chunk. Each retry runs inside its own savepoint, released on
    success so savepoints don't nest across the loop."""
    try:
        await run_in_threadpool(
            partial(
                uow.properties.bulk_insert,
                properties = [row["value"] for row in built_rows],
            )
        )
        await uow.commit()
        return len(built_rows), []
    except Exception as exc:
        await uow.rollback()
        logger.warning(
            "bulk_insert failed, falling back to row-by-row",
            extra={"total": len(built_rows)},
            exc_info=exc,
        )

    errors: list[BulkRowError] = []
    ok_count = 0

    for row in built_rows:
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

    return ok_count, errors
