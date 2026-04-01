import uuid
from typing import List

from sqlmodel import Session

from app.models.property import Property
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
