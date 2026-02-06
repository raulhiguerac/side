import uuid
from typing import List
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.location import Locality
from app.services.geo_catalog.ports.locality_repository import LocalityRepository

class SqlLocalityRepository(LocalityRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_by_country_id(
            self, 
            *, 
            country_id: uuid.UUID, 
        ) -> List[Locality]:

        stmt = (
            select(Locality)
            .options(selectinload(Locality.admin_division))
            .where(Locality.country_id == country_id)
            .where(Locality.is_active == True)
            .order_by(Locality.name)
        )

        return self.session.exec(stmt).all()

    def get_active_by_admin_division_id(
            self,
            *,
            admin_division_id: uuid.UUID,
        ) -> List[Locality]:

        stmt = (
            select(Locality)
            .options(selectinload(Locality.admin_division))
            .where(Locality.admin_division_id == admin_division_id)
            .where(Locality.is_active == True)
            .order_by(Locality.name)
        )

        return self.session.exec(stmt).all()