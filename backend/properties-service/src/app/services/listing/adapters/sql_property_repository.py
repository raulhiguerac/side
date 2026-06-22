import uuid
from typing import List

from sqlmodel import Session, select

from app.core.config.settings import settings
from app.models.property import ListingStatus, Property
from app.services.listing.ports.property_repository import (
    PropertyRepository,
)


class SqlPropertyRepository(PropertyRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def add(
            self, 
            *, 
            property: Property
        ) -> None:

        return self.session.add(property)
    
    def get_user_properties(
            self,
            *,
            user_id: uuid.UUID,
    ) -> List[Property]:
        stmt = (
            select(Property)
            .where(Property.owner_id == user_id)
            .where(Property.deleted_at.is_(None))
        )

        return self.session.exec(stmt).all()

    def get_public_user_properties(
            self,
            *,
            user_id: uuid.UUID,
            offset: int
    ) -> List[Property]:
        stmt = (
            select(Property)
            .where(Property.owner_id == user_id)
            .where(Property.status == ListingStatus.active)
            .where(Property.deleted_at.is_(None))
            .limit(settings.PUBLIC_PROPERTIES_PAGE_SIZE)
            .offset(offset)
        )

        return self.session.exec(stmt).all()

    def get_by_id(
            self,
            *,
            property_id: uuid.UUID,
    ) -> Property | None:
        stmt = (
            select(Property)
            .where(Property.id == property_id)
            .where(Property.deleted_at.is_(None))
        )

        return self.session.exec(stmt).first()

    def get_by_id_for_update(
            self,
            *,
            property_id: uuid.UUID,
    ) -> Property | None:
        stmt = (
            select(Property)
            .where(Property.id == property_id)
            .where(Property.deleted_at.is_(None))
            .with_for_update()
        )

        return self.session.exec(stmt).first()
