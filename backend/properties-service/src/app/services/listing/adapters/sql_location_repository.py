import uuid
from typing import List

from sqlmodel import Session

from app.models.property import PropertyLocation
from app.services.listing.ports.property_location_repository import (
    PropertyLocationRepository,
)


class SqlPropertyLocation(PropertyLocationRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def add(
            self, 
            *, 
            property: PropertyLocation
        ) -> None:

        return self.session.add(property)
