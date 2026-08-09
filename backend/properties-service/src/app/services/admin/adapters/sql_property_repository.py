import uuid
from typing import Optional

from sqlmodel import Session, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import noload

from app.models.listing import ListingStatus, Property, PropertyLocation, VerificationStatus
from app.models.image import PropertyImage
from app.models.promotion import PromotedListing, active_promotion_clause
from app.services.admin.ports.property_repository import AdminPropertyRepository

_PROPERTY_UPSERT_FIELDS = [
    "owner_id", "property_type", "listing_type", "condition", "status",
    "currency", "verification_status", "floor_number", "total_floors",
    "area_m2", "bedrooms", "bathrooms", "parking_spots", "h3_r9", "h3_r7",
    "description", "year_built", "admin_fee", "stratum", "price",
    "updated_at", "updated_by",
]

_LOCATION_UPSERT_FIELDS = [
    "neighborhood_id", "city_id", "country_id", "location",
    "updated_at", "updated_by",
]

_IMAGE_UPSERT_FIELDS = [
    "property_id", "status", "display_order", "is_cover",
    "updated_at", "updated_by",
]


class SqlAdminPropertyRepository(AdminPropertyRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def bulk_insert(self, *, properties: list[tuple[Property, PropertyLocation, list[PropertyImage]]]) -> None:
        prop_rows, location_rows, image_rows = [], [], []
        for prop, location, images in properties:
            prop_rows.append(prop.model_dump())
            location_rows.append(location.model_dump())
            image_rows.extend(img.model_dump() for img in images)

        prop_stmt = insert(Property).values(prop_rows)
        prop_stmt = prop_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={k: prop_stmt.excluded[k] for k in _PROPERTY_UPSERT_FIELDS},
        )
        self.session.exec(prop_stmt)

        loc_stmt = insert(PropertyLocation).values(location_rows)
        loc_stmt = loc_stmt.on_conflict_do_update(
            index_elements=["property_id"],
            set_={k: loc_stmt.excluded[k] for k in _LOCATION_UPSERT_FIELDS},
        )
        self.session.exec(loc_stmt)

        if image_rows:
            img_stmt = insert(PropertyImage).values(image_rows)
            img_stmt = img_stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={k: img_stmt.excluded[k] for k in _IMAGE_UPSERT_FIELDS},
            )
            self.session.exec(img_stmt)
    
    def add(self, *, property: tuple[Property, PropertyLocation, list[PropertyImage]]) -> None:
        prop, location, images = property

        prop_stmt = insert(Property).values(prop.model_dump())
        prop_stmt = prop_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={k: prop_stmt.excluded[k] for k in _PROPERTY_UPSERT_FIELDS},
        )
        self.session.exec(prop_stmt)

        loc_stmt = insert(PropertyLocation).values(location.model_dump())
        loc_stmt = loc_stmt.on_conflict_do_update(
            index_elements=["property_id"],
            set_={k: loc_stmt.excluded[k] for k in _LOCATION_UPSERT_FIELDS},
        )
        self.session.exec(loc_stmt)

        if images:
            img_stmt = insert(PropertyImage).values([img.model_dump() for img in images])
            img_stmt = img_stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={k: img_stmt.excluded[k] for k in _IMAGE_UPSERT_FIELDS},
            )
            self.session.exec(img_stmt)


    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None:
        stmt = select(Property).where(Property.id == property_id)
        return self.session.exec(stmt).first()

    def get_by_ids(self, *, property_ids: list[uuid.UUID]) -> list[Property]:
        if not property_ids:
            return []
        stmt = select(Property).where(Property.id.in_(property_ids))
        return list(self.session.exec(stmt).all())

    @staticmethod
    def _apply_filters(
        stmt,
        *,
        status: Optional[ListingStatus],
        verification_status: Optional[VerificationStatus],
        owner_id: Optional[uuid.UUID],
        is_promoted: Optional[bool],
    ):
        """Shared by get_all and count_all on purpose: a filter added to one and
        not the other would make the reported total disagree with the rows."""
        stmt = stmt.where(Property.deleted_at.is_(None))

        if status is not None:
            stmt = stmt.where(Property.status == status)
        if verification_status is not None:
            stmt = stmt.where(Property.verification_status == verification_status)
        if owner_id is not None:
            stmt = stmt.where(Property.owner_id == owner_id)
        if is_promoted is not None:
            # EXISTS y no JOIN: con join una property con varias promociones
            # duplicaría filas y rompería el count. La condición es la misma que
            # usa `get_active_by_property_id` —solo `is_active`, sin mirar
            # `ends_at`— porque es la que decide el DuplicateActivePromotionError.
            has_active_promotion = (
                select(PromotedListing.id)
                .where(PromotedListing.property_id == Property.id)
                .where(active_promotion_clause())
                .exists()
            )
            stmt = stmt.where(has_active_promotion if is_promoted else ~has_active_promotion)

        return stmt

    def get_all(
        self,
        *,
        status: Optional[ListingStatus] = None,
        verification_status: Optional[VerificationStatus] = None,
        owner_id: Optional[uuid.UUID] = None,
        is_promoted: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Property]:
        stmt = self._apply_filters(
            select(Property),
            status=status,
            verification_status=verification_status,
            owner_id=owner_id,
            is_promoted=is_promoted,
        )
        # Property eager-loads images, location and promotions with selectin, so
        # every page would also fetch image rows, PostGIS geometries and
        # promotions — none of which AdminPropertyCardSchema reads. Listed one by
        # one rather than raiseload("*") so re-enabling a single one (a thumbnail
        # column, say) is an obvious edit.
        stmt = stmt.options(
            noload(Property.images),
            noload(Property.location),
            noload(Property.promotions),
        )
        stmt = stmt.order_by(Property.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())

    def count_all(
        self,
        *,
        status: Optional[ListingStatus] = None,
        verification_status: Optional[VerificationStatus] = None,
        owner_id: Optional[uuid.UUID] = None,
        is_promoted: Optional[bool] = None,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count()).select_from(Property),
            status=status,
            verification_status=verification_status,
            owner_id=owner_id,
            is_promoted=is_promoted,
        )
        return self.session.exec(stmt).one()
