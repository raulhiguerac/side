import uuid
from typing import Optional

from sqlmodel import Session, select

from app.models.location import Locality
from app.services.catalog_admin.ports.locality_repository import LocalityAdminRepository


class SqlLocalityAdminRepository(LocalityAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, locality_id: uuid.UUID) -> Optional[Locality]:
        stmt = select(Locality).where(Locality.id == locality_id)
        return self.session.exec(stmt).first()

    def add(self, *, locality: Locality) -> Locality:
        self.session.add(locality)
        self.session.flush()
        return locality
