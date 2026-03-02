import uuid
from typing import Optional

from sqlalchemy import inspect, update
from sqlmodel import Session, select
from sqlalchemy.dialects.postgresql import insert

from app.models.location import Neighborhood
from app.services.catalog_admin.ports.neighborhood_repository import NeighborhoodAdminRepository

_EXCLUDED_FROM_UPSERT = {"id", "created_at", "updated_at", "geom", "h3_cells"}
_UPSERT_FIELDS = [
    c for c in inspect(Neighborhood).columns.keys() if c not in _EXCLUDED_FROM_UPSERT
]


class SqlNeighborhoodAdminRepository(NeighborhoodAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, neighborhood_id: uuid.UUID) -> Optional[Neighborhood]:
        stmt = select(Neighborhood).where(Neighborhood.id == neighborhood_id)
        return self.session.exec(stmt).first()
    
    def get_many_by_search_names(self, *, locality_id: uuid.UUID, search_names: list[str]) -> list[Neighborhood]:
        stmt =  select(Neighborhood) \
                .where(Neighborhood.locality_id == locality_id) \
                .where(Neighborhood.search_name.in_(search_names))
        return self.session.exec(stmt).all()

    def bulk_insert(self, *, neighborhoods: list[Neighborhood]) -> None:
        stmt = insert(Neighborhood).values([n.model_dump() for n in neighborhoods])
        stmt = stmt.on_conflict_do_update(
            constraint="uq_neighborhood_locality_code",
            set_={k: stmt.excluded[k] for k in _UPSERT_FIELDS},
        )
        self.session.execute(stmt)
        self.session.flush()
    
    def bulk_update(self, *, neighborhoods_geom: list[dict]) -> None:
        self.session.execute(update(Neighborhood), neighborhoods_geom)
        self.session.flush()

    def add(self, *, neighborhood: Neighborhood) -> Neighborhood:
        self.session.add(neighborhood)
        self.session.flush()
        return neighborhood
