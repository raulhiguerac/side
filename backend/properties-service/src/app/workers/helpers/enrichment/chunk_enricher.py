import asyncio
from collections.abc import Awaitable, Callable

from app.services.shared.ports.catalog_gateway import CatalogGateway
from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.enrichment.location_batch import process_location_batch
from app.workers.schemas.bulk_schemas import BulkRowError

ResolveEmails = Callable[[set[str]], Awaitable[list[ResolvedAccount]]]


async def enrich_chunk(
        rows: list[dict],
        *,
        catalog: CatalogGateway,
        resolve_emails: ResolveEmails,
        email_cache: dict[str, ResolvedAccount],
    ) -> tuple[list[dict], list[BulkRowError]]:
    """Resolves geo and owners for a chunk in parallel — they're independent
    network calls. Only emails missing from email_cache are requested, so an
    owner repeated across chunks costs a single round-trip for the whole run."""
    chunk_emails = {row["value"].email for row in rows}
    new_emails = chunk_emails - email_cache.keys()

    if new_emails:
        (enriched, location_errors), resolved = await asyncio.gather(
            process_location_batch(rows, catalog=catalog),
            resolve_emails(new_emails),
        )
        for account in resolved:
            email_cache[account.email] = account
    else:
        enriched, location_errors = await process_location_batch(rows, catalog=catalog)

    return enriched, location_errors
