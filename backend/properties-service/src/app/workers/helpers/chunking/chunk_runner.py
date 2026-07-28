import logging

from app.schemas.principal import Principal
from app.services.admin.ports.unit_of_work import AdminUnitOfWork
from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.enrichment.chunk_enricher import ResolveEmails, enrich_chunk
from app.workers.helpers.mapping.orm_objects import build_orm_objects
from app.workers.helpers.persistence.property_writer import persist_chunk
from app.workers.schemas.bulk_schemas import BulkRowError

logger = logging.getLogger(__name__)


async def process_chunk(
        rows: list[dict],
        *,
        principal: Principal,
        uow: AdminUnitOfWork,
        catalog: CatalogGateway,
        resolve_emails: ResolveEmails,
        email_cache: dict[str, ResolvedAccount],
    ) -> tuple[int, list[BulkRowError]]:
    """Full lifecycle of one chunk: enrich → map to ORM → persist. Runs to
    completion before the next chunk is read, so memory and transaction size
    stay bounded by the chunk, not by the file."""
    enriched, errors = await enrich_chunk(
        rows,
        catalog = catalog,
        resolve_emails = resolve_emails,
        email_cache = email_cache,
    )

    built_rows, build_errors = build_orm_objects(
        enriched,
        email_cache = email_cache,
        created_by = principal.sub,
    )
    errors.extend(build_errors)
    logger.info(
        "mapped chunk to orm",
        extra={"built": len(built_rows), "map_errors": len(build_errors)},
    )

    if not built_rows:
        logger.warning("chunk produced no rows to insert", extra={"errors": len(errors)})
        return 0, errors

    inserted, insert_errors = await persist_chunk(built_rows, uow=uow)
    errors.extend(insert_errors)

    return inserted, errors
