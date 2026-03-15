import uuid

from geoalchemy2.functions import ST_Point
from sqlalchemy import func, select, update
from sqlmodel import Session

from app.models.location import Country, Locality, Neighborhood
from app.services.geo_resolution.ports.georeferentiation_repository import (
    GeoreferentiationRepository,
)


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
        return self.session.scalars(stmt).first()
    
    def update_neighborhood_h3_cells(self, *, neighborhood_id: uuid.UUID, h3_index: str) -> None:
        stmt = (                                                                                           
            update(Neighborhood)
            .where(Neighborhood.id == neighborhood_id)                                                             
            .values(h3_cells=func.array_append(Neighborhood.h3_cells, h3_index))                        
        )
        self.session.execute(stmt)
        self.session.flush()

    def get_locality_country_code(self, *, locality_id: uuid.UUID) -> str | None:
        stmt = (
            select(Country.iso_alpha2)
            .join(Locality, Locality.country_id == Country.id)
            .where(Locality.id == locality_id)
        )
        return self.session.scalars(stmt).one_or_none()

    def get_locality_coordinates(self, *, locality_id: uuid.UUID) -> tuple[float, float] | None:
        stmt = select(Locality.latitude, Locality.longitude).where(Locality.id == locality_id)
        row = self.session.execute(stmt).first()
        if row is None:
            return None
        return row.latitude, row.longitude
