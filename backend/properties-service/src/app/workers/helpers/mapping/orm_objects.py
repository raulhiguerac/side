import uuid

from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.row_ref import row_ref
from app.workers.helpers.mapping.seed_mapper import build_models, row_to_item
from app.workers.schemas.bulk_schemas import BulkRowError


def build_orm_objects(
        rows: list[dict],
        *,
        email_cache: dict[str, ResolvedAccount],
        created_by: uuid.UUID,
    ) -> tuple[list[dict], list[BulkRowError]]:
    """Maps geo-enriched CSV rows into ORM objects, resolving each row's owner
    from email_cache. Keeps the row envelope (line/id/ref) around the built
    models so a failure downstream can still be traced back to its CSV line.
    Pure/sync so it's testable without a DB or gateway in the loop."""
    built: list[dict] = []
    errors: list[BulkRowError] = []

    for row in rows:
        value = row["value"]
        ref = row_ref(value.model_dump())

        account = email_cache.get(value.email)
        if account is None:
            errors.append(
                BulkRowError(
                    line = row["line"],
                    ref = ref,
                    issues = [f"owner not resolved for email: {value.email}"],
                )
            )
            continue

        image_urls = [u.strip() for u in value.image_urls.split(",") if u.strip()]

        item = row_to_item(
            row = value.model_dump(),
            neighborhood_id = row["neighborhood_id"],
            city_id = row["city_id"],
            country_id = row["country_id"],
            image_urls = image_urls,
        )
        if item is None:
            errors.append(
                BulkRowError(line=row["line"], ref=ref, issues=["row could not be mapped to a property"])
            )
            continue

        try:
            models = build_models(item=item, owner_id=account.account_id, created_by=created_by)
        except Exception as exc:
            errors.append(BulkRowError(line=row["line"], ref=ref, issues=[f"build error: {exc}"]))
            continue

        built.append(
            {
                "line": row["line"],
                "id": row["id"],
                "ref": ref,
                "value": models,
            }
        )

    return built, errors
