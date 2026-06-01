import uuid
from decimal import Decimal, InvalidOperation
from typing import Optional

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.models.property import (
    ImageStatus,
    ListingStatus,
    ListingType,
    Property,
    PropertyCondition,
    PropertyImage,
    PropertyLocation,
    PropertyType,
    VerificationStatus,
)
from app.services.admin.schemas.admin_schemas import BulkCreatePropertyItem
from app.services.shared.helpers.geometry import compute_h3

# =============================================================================
# Lookup tables
# =============================================================================

_TIPO_TO_PROPERTY_TYPE: dict[str, PropertyType] = {
    "apartamento": PropertyType.apartment,
    "apartaestudio": PropertyType.apartment,
    "casa": PropertyType.house,
    "casa lote": PropertyType.house,
    "casa campestre": PropertyType.house,
}

_TIPO_TO_LISTING_TYPE: dict[str, ListingType] = {
    "venta": ListingType.sale,
    "arriendo": ListingType.rent,
}

# 'menor a 1 año' is the only value that maps to new
_ANTIGUEDAD_TO_CONDITION: dict[str, PropertyCondition] = {
    "menor a 1 año": PropertyCondition.new,
    "1 a 8 años": PropertyCondition.used,
    "9 a 15 años": PropertyCondition.used,
    "16 a 30 años": PropertyCondition.used,
    "más de 30 años": PropertyCondition.used,
    "sin especificar": PropertyCondition.used,
}

# =============================================================================
# Field parsers
# =============================================================================

def parse_property_type(value: str) -> Optional[PropertyType]:
    return _TIPO_TO_PROPERTY_TYPE.get(value.strip().lower())


def parse_listing_type(value: str) -> Optional[ListingType]:
    return _TIPO_TO_LISTING_TYPE.get(value.strip().lower())


def parse_condition(antiguedad: str) -> PropertyCondition:
    return _ANTIGUEDAD_TO_CONDITION.get(antiguedad.strip().lower(), PropertyCondition.used)


def parse_floor_number(piso: str) -> Optional[int]:
    """'2°' → 2 | 'Sin especificar' | 'Otro' → None"""
    cleaned = piso.strip()
    if cleaned.lower() in ("sin especificar", "otro", ""):
        return None
    try:
        return int(cleaned.rstrip("°").rstrip("º"))
    except ValueError:
        return None


def parse_parking(value: str) -> int:
    """'Sin especificar' → 0 | 'Más de 10' → 10 | else int"""
    cleaned = value.strip()
    if cleaned.lower() in ("sin especificar", ""):
        return 0
    if cleaned.lower().startswith("más de"):
        try:
            return int(cleaned.split()[-1])
        except ValueError:
            return 0
    try:
        return int(cleaned)
    except ValueError:
        return 0


def parse_bathrooms(value: str) -> Decimal:
    """'Sin especificar' → Decimal('1') | else Decimal"""
    cleaned = value.strip()
    if cleaned.lower() in ("sin especificar", ""):
        return Decimal("1")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("1")


def parse_stratum(value: str) -> Optional[int]:
    """'0' | 'especificar' → None | '1'-'6' → int"""
    cleaned = value.strip()
    if cleaned.lower() in ("sin especificar", "especificar", "0", ""):
        return None
    try:
        v = int(cleaned)
        return v if 1 <= v <= 6 else None
    except ValueError:
        return None


def parse_admin_fee(value: str) -> Optional[Decimal]:
    try:
        d = Decimal(value.strip())
        return d if d > 0 else None
    except InvalidOperation:
        return None


# =============================================================================
# Row → BulkCreatePropertyItem
# =============================================================================

def row_to_item(
    row: dict,
    *,
    neighborhood_id: uuid.UUID,
    city_id: uuid.UUID,
    country_id: uuid.UUID,
    image_urls: list[str],
) -> Optional[BulkCreatePropertyItem]:
    """
    Map a raw CSV row (enriched with catalog IDs) to BulkCreatePropertyItem.
    Returns None for rows that can't be mapped (unknown property_type, bad numbers).
    """
    property_type = parse_property_type(row.get("tipo_propiedad", ""))
    if property_type is None:
        return None

    listing_type = parse_listing_type(row.get("tipo", ""))
    if listing_type is None:
        return None

    try:
        area_m2 = Decimal(str(row["area_m2"]))
        price = Decimal(str(row["precio"]))
        bedrooms = int(row["cuartos"])
        lat = float(row["lat"])
        lon = float(row["lon"])
    except (KeyError, ValueError, InvalidOperation):
        return None

    if bedrooms < 1 or area_m2 <= 0 or price <= 0:
        return None

    return BulkCreatePropertyItem(
        property_type=property_type,
        listing_type=listing_type,
        condition=parse_condition(row.get("antiguedad", "")),
        area_m2=area_m2,
        bedrooms=bedrooms,
        bathrooms=parse_bathrooms(row.get("banios", "")),
        parking_spots=parse_parking(row.get("parqueaderos", "")),
        floor_number=parse_floor_number(row.get("piso", "")),
        stratum=parse_stratum(row.get("estrato", "")),
        price=price,
        admin_fee=parse_admin_fee(row.get("precio_admin", "0")),
        description=row.get("descripcion") or None,
        latitude=lat,
        longitude=lon,
        neighborhood_id=neighborhood_id,
        city_id=city_id,
        country_id=country_id,
        image_urls=image_urls,
    )


# =============================================================================
# BulkCreatePropertyItem → ORM objects
# =============================================================================

def build_models(
    *,
    item: BulkCreatePropertyItem,
    owner_id: uuid.UUID,
    created_by: uuid.UUID,
) -> tuple[Property, PropertyLocation, list[PropertyImage]]:
    """
    Build ORM objects from an enriched BulkCreatePropertyItem.

    Seed-specific defaults:
    - Apartments with no piso → floor_number = 0
    - Houses with no floor data → total_floors = 1
    - Currency always COP
    - Status always active (seed is published data)
    """
    property_id = uuid.uuid4()
    h3_r9, h3_r7 = compute_h3(item.latitude, item.longitude)

    floor_number = item.floor_number
    total_floors = item.total_floors
    if item.property_type == PropertyType.apartment and floor_number is None:
        floor_number = 0
    if item.property_type == PropertyType.house and total_floors is None:
        total_floors = 1

    prop = Property(
        id=property_id,
        owner_id=owner_id,
        property_type=item.property_type,
        listing_type=item.listing_type,
        condition=item.condition,
        currency="COP",
        status=ListingStatus.active,
        verification_status=VerificationStatus.unverified,
        floor_number=floor_number,
        total_floors=total_floors,
        area_m2=item.area_m2,
        bedrooms=item.bedrooms,
        bathrooms=item.bathrooms,
        parking_spots=item.parking_spots,
        h3_r9=h3_r9,
        h3_r7=h3_r7,
        price=item.price,
        admin_fee=item.admin_fee,
        description=item.description,
        year_built=item.year_built,
        stratum=item.stratum,
        created_by=created_by,
        updated_by=created_by,
    )

    location = PropertyLocation(
        property_id=property_id,
        neighborhood_id=item.neighborhood_id,
        city_id=item.city_id,
        country_id=item.country_id,
        location=from_shape(Point(item.longitude, item.latitude), srid=4326),
        created_by=created_by,
        updated_by=created_by,
    )

    images = [
        PropertyImage(
            property_id=property_id,
            url=url,
            status=ImageStatus.active,
            display_order=i,
            is_cover=(i == 0),
            created_by=created_by,
            updated_by=created_by,
        )
        for i, url in enumerate(item.image_urls)
    ]

    return prop, location, images
