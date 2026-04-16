import uuid
from typing import Optional

from sqlmodel import Session, select

from app.models.property import ListingStatus, Property, VerificationStatus


class SqlAdminPropertyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None:
        stmt = select(Property).where(Property.id == property_id)
        return self.session.exec(stmt).first()

    def get_by_ids(self, *, property_ids: list[uuid.UUID]) -> list[Property]:
        if not property_ids:
            return []
        stmt = select(Property).where(Property.id.in_(property_ids))
        return list(self.session.exec(stmt).all())

    def get_all(
        self,
        *,
        status: Optional[ListingStatus] = None,
        verification_status: Optional[VerificationStatus] = None,
        owner_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Property]:
        stmt = select(Property).where(Property.deleted_at.is_(None))

        if status is not None:
            stmt = stmt.where(Property.status == status)
        if verification_status is not None:
            stmt = stmt.where(Property.verification_status == verification_status)
        if owner_id is not None:
            stmt = stmt.where(Property.owner_id == owner_id)

        stmt = stmt.order_by(Property.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())
