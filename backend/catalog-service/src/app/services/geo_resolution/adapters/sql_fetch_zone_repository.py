from sqlmodel import select, Session

from app.models.location import FetchZone
from app.services.geo_resolution.ports.fetch_zone_repository import FetchZoneRepository


class SqlFetchZoneRepository(FetchZoneRepository):

    def __init__(self, session: Session):
        self.session = session

    def get_by_geohash(self, *, geohash: str) -> FetchZone | None:
        stmt = select(FetchZone).where(FetchZone.geohash == geohash)
        return self.session.exec(stmt).first()

    def add(self, *, fetch_zone: FetchZone) -> None:
        self.session.add(fetch_zone)
        self.session.flush()
