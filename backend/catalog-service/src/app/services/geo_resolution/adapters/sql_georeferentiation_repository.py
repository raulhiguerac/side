import uuid
from sqlmodel import Session
from sqlalchemy import select, func
from geoalchemy2.functions import ST_Point
from app.models.location import Country, Locality, Neighborhood
from app.services.geo_resolution.ports.georeferentiation_repository import GeoreferentiationRepository

class SqlGeoreferentiationRepository(GeoreferentiationRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_neighborhood_by_coordinates(
              self,
              *,
              lat: float,
              lon: float,
              locality_id: uuid.UUID
        ) -> Neighborhood | None:
        pnt = func.ST_SetSRID(ST_Point(lon, lat), 4326)
        stmt = (
            select(Neighborhood)
            .where(Neighborhood.locality_id == locality_id)
            .filter(func.ST_Contains(Neighborhood.geom, pnt))
        )
        return self.session.exec(stmt).first()

    def get_locality_country_code(self, *, locality_id: uuid.UUID) -> str | None:
        stmt = (
            select(Country.iso_alpha2)
            .join(Locality, Locality.country_id == Country.id)
            .where(Locality.id == locality_id)
        )
        return self.session.exec(stmt).first()
