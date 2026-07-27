import uuid

import pytest

from app.workers.helpers.mapping.seed_mapper import (
    build_models,
    derive_property_id,
    parse_bathrooms,
    parse_condition,
    parse_floor_number,
    parse_parking,
    parse_stratum,
    row_to_item,
)
from app.models.listing import ListingStatus, PropertyCondition, PropertyType

NEIGHBORHOOD_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CITY_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
COUNTRY_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
OWNER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


def _row(**overrides) -> dict:
    row = {
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
        "email": "owner@test.com",
    }
    row.update(overrides)
    return row


def _to_item(**overrides):
    return row_to_item(
        row=_row(**overrides),
        neighborhood_id=NEIGHBORHOOD_ID,
        city_id=CITY_ID,
        country_id=COUNTRY_ID,
        image_urls=[],
    )


# ---------------------------------------------------------------------------
# derive_property_id — this is what makes a re-import upsert instead of duplicate
# ---------------------------------------------------------------------------

def test_same_external_id_yields_same_id():
    assert derive_property_id(external_id="CSV-001") == derive_property_id(external_id="CSV-001")


def test_different_external_id_yields_different_id():
    assert derive_property_id(external_id="CSV-001") != derive_property_id(external_id="CSV-002")


def test_id_is_stable_across_namespace_reads(monkeypatch):
    from app.core.config.settings import settings

    monkeypatch.setattr(settings, "BULK_PROPERTY_ID_NAMESPACE", uuid.UUID(int=1))
    first = derive_property_id(external_id="CSV-001")
    monkeypatch.setattr(settings, "BULK_PROPERTY_ID_NAMESPACE", uuid.UUID(int=2))
    second = derive_property_id(external_id="CSV-001")

    # Namespace is part of the derivation — changing it re-keys everything,
    # which is exactly why it's documented as frozen.
    assert first != second


def test_reimport_of_same_row_builds_same_property_id():
    ids = []
    for _ in range(2):
        item = _to_item()
        prop, location, _ = build_models(item=item, owner_id=OWNER_ID, created_by=OWNER_ID)
        ids.append((prop.id, location.property_id))

    assert ids[0] == ids[1]
    assert ids[0][0] == ids[0][1]  # location points at the same property


# ---------------------------------------------------------------------------
# row_to_item — rows that can't be mapped return None instead of raising
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "overrides",
    [
        {"external_id": ""},            # blank key would collide with every other blank
        {"external_id": "   "},
        {"tipo_propiedad": "bodega"},   # unknown property type
        {"tipo": "permuta"},            # unknown listing type
        {"area_m2": "abc"},             # unparseable number
        {"cuartos": "0"},               # bedrooms < 1
        {"precio": "0"},                # price <= 0
    ],
)
def test_unmappable_rows_return_none(overrides):
    assert _to_item(**overrides) is None


def test_maps_a_valid_row():
    item = _to_item()

    assert item.external_id == "CSV-001"
    assert item.property_type == PropertyType.apartment
    assert item.bedrooms == 3
    assert item.neighborhood_id == NEIGHBORHOOD_ID


# ---------------------------------------------------------------------------
# Tolerant parsers — the placeholder values that show up in the source data
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [("Sin especificar", 0), ("Más de 10", 10), ("3", 3), ("basura", 0)],
)
def test_parse_parking(raw, expected):
    assert parse_parking(raw) == expected


@pytest.mark.parametrize("raw,expected", [("Sin especificar", 1), ("2.5", 2.5), ("basura", 1)])
def test_parse_bathrooms(raw, expected):
    assert float(parse_bathrooms(raw)) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("0", None), ("Sin especificar", None), ("7", None), ("4", 4)],
)
def test_parse_stratum(raw, expected):
    assert parse_stratum(raw) == expected


@pytest.mark.parametrize("raw,expected", [("2°", 2), ("Sin especificar", None), ("Otro", None)])
def test_parse_floor_number(raw, expected):
    assert parse_floor_number(raw) == expected


def test_parse_condition_defaults_to_used():
    assert parse_condition("menor a 1 año") == PropertyCondition.new
    assert parse_condition("cualquier cosa") == PropertyCondition.used


# ---------------------------------------------------------------------------
# build_models — seed-specific defaults
# ---------------------------------------------------------------------------

def test_apartment_without_floor_defaults_to_zero():
    item = _to_item(piso="Sin especificar")
    prop, _, _ = build_models(item=item, owner_id=OWNER_ID, created_by=OWNER_ID)

    assert prop.property_type == PropertyType.apartment
    assert prop.floor_number == 0


def test_house_without_floors_defaults_to_one():
    item = _to_item(tipo_propiedad="casa", piso="Sin especificar")
    prop, _, _ = build_models(item=item, owner_id=OWNER_ID, created_by=OWNER_ID)

    assert prop.total_floors == 1


def test_seed_rows_are_published_in_cop():
    prop, _, _ = build_models(item=_to_item(), owner_id=OWNER_ID, created_by=OWNER_ID)

    assert prop.currency == "COP"
    assert prop.status == ListingStatus.active
    assert prop.owner_id == OWNER_ID


def test_first_image_is_cover_and_order_is_preserved():
    item = row_to_item(
        row=_row(),
        neighborhood_id=NEIGHBORHOOD_ID,
        city_id=CITY_ID,
        country_id=COUNTRY_ID,
        image_urls=["a.jpg", "b.jpg", "c.jpg"],
    )
    _, _, images = build_models(item=item, owner_id=OWNER_ID, created_by=OWNER_ID)

    assert [img.url for img in images] == ["a.jpg", "b.jpg", "c.jpg"]
    assert [img.display_order for img in images] == [0, 1, 2]
    assert [img.is_cover for img in images] == [True, False, False]
