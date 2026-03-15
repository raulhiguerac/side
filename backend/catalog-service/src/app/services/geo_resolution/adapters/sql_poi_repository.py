import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, select

from app.models.location import PointOfInterest
from app.services.geo_resolution.ports.poi_repository import PoiRepository

UPSERT_FIELDS = {
    "name", "search_name", "full_address", "category", "subcategories",
    "latitude", "longitude", "h3_index", "phone", "website",
    "raw_response", "fetched_at", "is_stale",
}

class SqlPoiRepository(PoiRepository):
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_external_id(self, *, external_id: str, source: str) -> PointOfInterest | None:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.external_id == external_id) \
                .where(PointOfInterest.source == source)
        return self.session.exec(stmt).first()
    
    def get_active_by_locality_id(self, *, locality_id: uuid.UUID) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.locality_id == locality_id) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()
    
    def get_by_h3_index(self, *, h3_index: str) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.h3_index == h3_index) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()

    def get_by_h3_cells(self, *, h3_cells: list[str]) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(col(PointOfInterest.h3_index).in_(h3_cells)) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()

    def search_by_name(self, *, search_name: str, locality_id: uuid.UUID) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.locality_id == locality_id) \
                .where(col(PointOfInterest.search_name).contains(search_name)) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()
    
    def _to_dict(self, poi: PointOfInterest) -> dict:
        return {k: v for k, v in poi.model_dump().items() if v is not None}

    def add(self, *, poi: PointOfInterest) -> None:
        stmt = insert(PointOfInterest).values(self._to_dict(poi))
        stmt = stmt.on_conflict_do_update(
            constraint="uq_poi_external_id_source",
            set_={k: stmt.excluded[k] for k in UPSERT_FIELDS},
        )
        self.session.execute(stmt)
        self.session.flush()

    def add_many(self, *, pois: list[PointOfInterest]) -> None:
        if not pois:
            return
        stmt = insert(PointOfInterest).values([self._to_dict(p) for p in pois])
        stmt = stmt.on_conflict_do_update(
            constraint="uq_poi_external_id_source",
            set_={k: stmt.excluded[k] for k in UPSERT_FIELDS},
        )
        self.session.execute(stmt)
        self.session.flush()