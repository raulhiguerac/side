import uuid
from typing import Optional

from geoalchemy2.functions import ST_Point
from sqlalchemy import case, cast, func, literal, select, true, update
from sqlalchemy.dialects.postgresql import ARRAY, DOUBLE_PRECISION, TEXT
from sqlmodel import Session

from app.models.location import Country, Locality, Neighborhood
from app.services.geo_resolution.ports.sql.georeferentiation_repository import (
    GeoreferentiationRepository,
)
from app.services.geo_resolution.schemas.neighborhood import (
    LocationByCoordinates,
    PointToResolve,
    ResolvedPoint,
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
            .values(
                h3_cells=case(
                    (Neighborhood.h3_cells.any(h3_index), Neighborhood.h3_cells),
                    else_=func.array_append(Neighborhood.h3_cells, h3_index),
                )
            )
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

    def get_location_by_point(self, *, lat: float, lon: float, cell: str) -> Optional[LocationByCoordinates]:
        pnt = func.ST_SetSRID(ST_Point(lon, lat), 4326)

        # Prefiltro por h3_cells (índice GIN) para acotar candidatos antes del
        # ST_Contains — una celda puede solapar 2-3 barrios cerca de un borde,
        # así que el ST_Contains sigue siendo el que decide el barrio correcto.
        narrowed_stmt = (
            select(Neighborhood.id, Neighborhood.locality_id, Locality.country_id)
            .join(Locality, Locality.id == Neighborhood.locality_id)
            .where(Neighborhood.h3_cells.any(cell))
            .filter(func.ST_Contains(Neighborhood.geom, pnt))
            .limit(1)
        )
        row = self.session.execute(narrowed_stmt).first()

        if row is None:
            # Celda fría (nunca poblada): sin candidatos para acotar, hay que
            # barrer todos los barrios con geom.
            full_stmt = (
                select(Neighborhood.id, Neighborhood.locality_id, Locality.country_id)
                .join(Locality, Locality.id == Neighborhood.locality_id)
                .where(Neighborhood.geom.isnot(None))
                .filter(func.ST_Contains(Neighborhood.geom, pnt))
                .limit(1)
            )
            row = self.session.execute(full_stmt).first()

        if row is None:
            return None
        return LocationByCoordinates(
            neighborhood_id=row[0],
            locality_id=row[1],
            country_id=row[2],
        )
    
    def get_location_by_points(
            self, *, points: list[PointToResolve]
        ) -> list[ResolvedPoint]:
        if not points:
            return []

        results: dict[str, Optional[LocationByCoordinates]] = {p.id: None for p in points}

        for point_id, neighborhood_id, locality_id, country_id in self._match_points(points, use_h3_prefilter=True):
            if neighborhood_id is not None:
                results[point_id] = LocationByCoordinates(
                    neighborhood_id=neighborhood_id, locality_id=locality_id, country_id=country_id,
                )

        # Celdas frías (nunca pobladas): sin candidatos para acotar por h3_cells,
        # hay que barrer todos los barrios con geom para esos puntos.
        missed = [p for p in points if results[p.id] is None]
        if missed:
            for point_id, neighborhood_id, locality_id, country_id in self._match_points(missed, use_h3_prefilter=False):
                if neighborhood_id is not None:
                    results[point_id] = LocationByCoordinates(
                        neighborhood_id=neighborhood_id, locality_id=locality_id, country_id=country_id,
                    )

        return [ResolvedPoint(id=p.id, location=results[p.id]) for p in points]

    def _match_points(self, points: list[PointToResolve], *, use_h3_prefilter: bool):
        """Resuelve un batch de puntos en una sola query: unnest + LATERAL JOIN,
        un ST_Contains por punto en vez de N round-trips."""
        ids = cast(literal([p.id for p in points]), ARRAY(TEXT))
        lats = cast(literal([p.lat for p in points]), ARRAY(DOUBLE_PRECISION))
        lons = cast(literal([p.lon for p in points]), ARRAY(DOUBLE_PRECISION))

        if use_h3_prefilter:
            cells = cast(literal([p.cell for p in points]), ARRAY(TEXT))
            pts = func.unnest(ids, lats, lons, cells).table_valued("id", "lat", "lon", "cell").render_derived()
        else:
            pts = func.unnest(ids, lats, lons).table_valued("id", "lat", "lon").render_derived()

        pnt = func.ST_SetSRID(ST_Point(pts.c.lon, pts.c.lat), 4326)

        match_query = (
            select(Neighborhood.id.label("neighborhood_id"), Neighborhood.locality_id, Locality.country_id)
            .join(Locality, Locality.id == Neighborhood.locality_id)
            .where(func.ST_Contains(Neighborhood.geom, pnt))
        )
        match_query = (
            match_query.where(Neighborhood.h3_cells.any(pts.c.cell))
            if use_h3_prefilter
            else match_query.where(Neighborhood.geom.isnot(None))
        )
        match = match_query.limit(1).lateral("match")

        stmt = (
            select(pts.c.id, match.c.neighborhood_id, match.c.locality_id, match.c.country_id)
            .select_from(pts)
            .outerjoin(match, true())
        )
        return self.session.execute(stmt).all()
