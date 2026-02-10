import uuid
from typing import List
from sqlmodel import Session, select

from app.models.location import Neighborhood
from app.services.geo_catalog.ports.neighborhood_repository import NeighborhoodRepository

class SqlNeighborhoodRepository(NeighborhoodRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_by_locality_id(
            self, 
            *, 
            locality_id: uuid.UUID
        ) -> List[Neighborhood]:

        stmt = (
            select(Neighborhood)
            .where(Neighborhood.locality_id == locality_id)
            .where(Neighborhood.is_active == True)
            .order_by(Neighborhood.name)
        )

        return self.session.exec(stmt).all()
    
    def get_active_by_id(self,
            *,
            neighborhood_id: uuid.UUID,
        ) -> Neighborhood:

        stmt = (
            select(Neighborhood)
            .where(Neighborhood.id == neighborhood_id)
            .where(Neighborhood.is_active == True)
        )

        return self.session.exec(stmt).first()