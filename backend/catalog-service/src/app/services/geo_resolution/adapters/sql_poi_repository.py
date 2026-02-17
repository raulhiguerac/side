import uuid
from sqlmodel import select, Session, col

from app.models.location import PointOfInterest
from app.services.geo_resolution.ports.poi_repository import PoiRepository

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
    
    def get_by_geohash(self, *, geohash: str) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.geohash == geohash) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()
    
    def get_by_neighborhood_geohashes(self, *, geohashes: list[str]) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(col(PointOfInterest.geohash).in_(geohashes)) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()

    def search_by_name(self, *, search_name: str, locality_id: uuid.UUID) -> list[PointOfInterest]:
        stmt =  select(PointOfInterest) \
                .where(PointOfInterest.locality_id == locality_id) \
                .where(col(PointOfInterest.search_name).contains(search_name)) \
                .where(PointOfInterest.is_active == True)
        return self.session.exec(stmt).all()
    
    def add(self, *, poi: PointOfInterest) -> None:
        self.session.add(poi)
        self.session.flush()

    def add_many(self, *, pois: list[PointOfInterest]) -> None:
        self.session.add_all(pois)
        self.session.flush()