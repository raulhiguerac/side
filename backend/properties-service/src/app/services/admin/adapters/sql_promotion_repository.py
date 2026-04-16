import uuid
from typing import Optional

from sqlmodel import Session, select

from app.models.property import PromotedListing


class SqlPromotionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, *, promotion: PromotedListing) -> None:
        self.session.add(promotion)
        self.session.flush()

    def flush(self) -> None:
        self.session.flush()

    def get_active_by_property_id(self, *, property_id: uuid.UUID) -> PromotedListing | None:
        stmt = (
            select(PromotedListing)
            .where(PromotedListing.property_id == property_id)
            .where(PromotedListing.is_active == True)  # noqa: E712
        )
        return self.session.exec(stmt).first()

    def get_all(self, *, property_id: Optional[uuid.UUID] = None) -> list[PromotedListing]:
        stmt = select(PromotedListing)
        if property_id is not None:
            stmt = stmt.where(PromotedListing.property_id == property_id)
        return list(self.session.exec(stmt).all())

    def delete(self, *, promotion: PromotedListing) -> None:
        self.session.delete(promotion)
        self.session.flush()
