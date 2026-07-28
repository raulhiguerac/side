import uuid

from app.services.shared.schemas.users_schemas import ResolvedAccount
from app.workers.helpers.mapping.orm_objects import build_orm_objects
from app.workers.schemas.bulk_schemas import BulkPropertyCsvRow

NEIGHBORHOOD_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CITY_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
COUNTRY_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
CREATED_BY = uuid.UUID("44444444-4444-4444-4444-444444444444")
ACCOUNT_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")

EMAIL = "owner@test.com"


def _csv_row(**overrides) -> BulkPropertyCsvRow:
    fields = {
        "external_id": "CSV-001",
        "area_m2": "80",
        "cuartos": "3",
        "estrato": "4",
        "tipo": "venta",
        "parqueaderos": "1",
        "banios": "2",
        "piso": "3",
        "precio": "350000000",
        "precio_admin": "250000",
        "tipo_propiedad": "apartamento",
        "lat": 4.65,
        "lon": -74.05,
        "antiguedad": "1 a 8 años",
        "descripcion": "",
        "image_urls": "",
        "email": EMAIL,
    }
    fields.update(overrides)
    return BulkPropertyCsvRow(**fields)


def _enriched_row(line: int = 2, **overrides) -> dict:
    return {
        "line": line,
        "id": str(uuid.uuid4()),
        "value": _csv_row(**overrides),
        "neighborhood_id": NEIGHBORHOOD_ID,
        "city_id": CITY_ID,
        "country_id": COUNTRY_ID,
    }


def _cache(email: str = EMAIL) -> dict[str, ResolvedAccount]:
    return {email: ResolvedAccount(account_id=ACCOUNT_ID, email=email)}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_builds_models_and_keeps_the_row_envelope():
    built, errors = build_orm_objects([_enriched_row(line=7)], email_cache=_cache(), created_by=CREATED_BY)

    assert errors == []
    assert len(built) == 1
    # line/id/ref survive so a failure downstream can still name the CSV line
    assert built[0]["line"] == 7
    assert "id" in built[0]
    assert EMAIL in built[0]["ref"]

    prop, location, _ = built[0]["value"]
    assert prop.owner_id == ACCOUNT_ID
    assert prop.created_by == CREATED_BY
    assert location.neighborhood_id == NEIGHBORHOOD_ID


def test_splits_comma_separated_image_urls():
    row = _enriched_row(image_urls=" a.jpg , b.jpg ,, c.jpg ")
    built, _ = build_orm_objects([row], email_cache=_cache(), created_by=CREATED_BY)

    _, _, images = built[0]["value"]
    assert [img.url for img in images] == ["a.jpg", "b.jpg", "c.jpg"]


# ---------------------------------------------------------------------------
# Owner resolution — an unresolved email must never fall back to another owner
# ---------------------------------------------------------------------------

def test_unresolved_owner_becomes_a_row_error():
    built, errors = build_orm_objects(
        [_enriched_row(line=5, email="ghost@test.com")],
        email_cache=_cache(),
        created_by=CREATED_BY,
    )

    assert built == []
    assert len(errors) == 1
    assert errors[0].line == 5
    assert "ghost@test.com" in errors[0].issues[0]


def test_owner_lookup_is_case_sensitive():
    """Documents current behaviour: the CSV casing must match the account's."""
    built, errors = build_orm_objects(
        [_enriched_row(email="Owner@Test.com")],
        email_cache=_cache(EMAIL),
        created_by=CREATED_BY,
    )

    assert built == []
    assert len(errors) == 1


# ---------------------------------------------------------------------------
# Partial failure — one bad row must not cost the rest of the chunk
# ---------------------------------------------------------------------------

def test_unmappable_row_is_reported_and_the_rest_survive():
    rows = [
        _enriched_row(line=2),
        _enriched_row(line=3, tipo_propiedad="bodega"),  # unknown type
        _enriched_row(line=4),
    ]

    built, errors = build_orm_objects(rows, email_cache=_cache(), created_by=CREATED_BY)

    assert len(built) == 2
    assert [row["line"] for row in built] == [2, 4]
    assert len(errors) == 1
    assert errors[0].line == 3


def test_empty_input_is_not_an_error():
    built, errors = build_orm_objects([], email_cache=_cache(), created_by=CREATED_BY)

    assert built == []
    assert errors == []
