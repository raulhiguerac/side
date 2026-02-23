import uuid
from typing import Optional

from sqlmodel import Session, select

from app.models.location import Neighborhood
from app.services.catalog_admin.ports.neighborhood_repository import NeighborhoodAdminRepository


class SqlNeighborhoodAdminRepository(NeighborhoodAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, neighborhood_id: uuid.UUID) -> Optional[Neighborhood]:
        stmt = select(Neighborhood).where(Neighborhood.id == neighborhood_id)
        return self.session.exec(stmt).first()

    def add(self, *, neighborhood: Neighborhood) -> Neighborhood:
        self.session.add(neighborhood)
        self.session.flush()
        return neighborhood
