import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import tuple_
from sqlmodel import Session, select

from app.models.listing import ListingStatus, Property, PropertyLocation, PropertyType
from app.models.promotion import PromotedListing
from app.services.search.ports.property_search_repository import PropertySearchRepository


class SqlPropertySearchRepository(PropertySearchRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_properties(
        self,
        *,
        city_ids: list[uuid.UUID] | None = None,
        neighborhood_ids: list[uuid.UUID] | None = None,
        property_types: list[PropertyType] | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_area_m2: Decimal | None = None,
        max_area_m2: Decimal | None = None,
        min_bathrooms: Decimal | None = None,
        bedrooms: int | None = None,
        promoted_only: bool = False,
        cursor_created_at: datetime | None = None,
        cursor_id: uuid.UUID | None = None,
        limit: int = 60,
    ) -> list[Property]:
        stmt = (
            select(Property)
            .join(PropertyLocation, PropertyLocation.property_id == Property.id)
            .where(Property.status == ListingStatus.active)
            .where(Property.deleted_at.is_(None))
        )

        if city_ids:
            stmt = stmt.where(PropertyLocation.city_id.in_(city_ids))

        if neighborhood_ids:
            stmt = stmt.where(PropertyLocation.neighborhood_id.in_(neighborhood_ids))

        if property_types:
            stmt = stmt.where(Property.property_type.in_(property_types))

        if min_price is not None:
            stmt = stmt.where(Property.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Property.price <= max_price)

        if min_area_m2 is not None:
            stmt = stmt.where(Property.area_m2 >= min_area_m2)

        if max_area_m2 is not None:
            stmt = stmt.where(Property.area_m2 <= max_area_m2)

        if min_bathrooms is not None:
            stmt = stmt.where(Property.bathrooms >= min_bathrooms)

        if bedrooms is not None:
            stmt = stmt.where(Property.bedrooms == bedrooms)

        if promoted_only:
            stmt = stmt.join(
                PromotedListing, PromotedListing.property_id == Property.id
            ).where(
                PromotedListing.is_active == True  # noqa: E712
            ).order_by(PromotedListing.priority.desc(), Property.created_at.desc(), Property.id.desc())
        else:
            stmt = stmt.order_by(Property.created_at.desc(), Property.id.desc())

        # Keyset cursor — solo para orgánicos (promoted usa priority, no tiene cursor estable)
        if not promoted_only and cursor_created_at is not None and cursor_id is not None:
            stmt = stmt.where(
                tuple_(Property.created_at, Property.id) < (cursor_created_at, cursor_id)
            )

        stmt = stmt.limit(limit)

        return self.session.exec(stmt).all()
    
    def get_by_bbox(self, *, h3_indexes: list[str], resolution: int) -> list[Property]:
        if not h3_indexes:
            return []

        if resolution == 7:
            h3_filter = Property.h3_r7.in_(h3_indexes)
        elif resolution == 9:
            h3_filter = Property.h3_r9.in_(h3_indexes)
        else:
            return []

        stmt = (
            select(Property)
            .where(Property.status == ListingStatus.active)
            .where(Property.deleted_at.is_(None))
            .where(h3_filter)
        )

        return self.session.exec(stmt).all()
