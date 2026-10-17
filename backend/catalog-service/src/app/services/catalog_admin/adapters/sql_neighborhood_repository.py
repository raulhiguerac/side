import unicodedata
import uuid

from geoalchemy2 import Geography
from geoalchemy2.functions import (
    ST_Area,
    ST_AsGeoJSON,
    ST_AsSVG,
    ST_ClipByBox2D,
    ST_Intersects,
    ST_MakeEnvelope,
    ST_SimplifyPreserveTopology,
    ST_XMax,
    ST_XMin,
    ST_YMax,
    ST_YMin,
)
from sqlalchemy import JSON, Select, case, cast, func, inspect, update
from sqlalchemy.dialects.postgresql import array, insert
from sqlmodel import Session, select

from app.models.location import Neighborhood
from app.services.catalog_admin.ports.neighborhood_repository import (
    NeighborhoodAdminRepository,
)
from app.services.catalog_admin.schemas.neighborhood import (
    ListNeighborhoodGeometriesRequest,
    ListNeighborhoodsAdminRequest,
    NeighborhoodAdminDetail,
    NeighborhoodAdminListItem,
    NeighborhoodCoverage,
    NeighborhoodGeometryItem,
)

_EXCLUDED_FROM_UPSERT = {"id", "created_at", "updated_at", "geom", "h3_cells"}
_UPSERT_FIELDS = [
    c for c in inspect(Neighborhood).columns.keys() if c not in _EXCLUDED_FROM_UPSERT  # noqa: SIM118 (.columns itera Column, no keys)
]

_SIMPLIFY_TOLERANCE = 0.00001


def _apply_filters(stmt: Select, req: ListNeighborhoodsAdminRequest) -> Select:
    if req.locality_id:
        stmt = stmt.where(Neighborhood.locality_id == req.locality_id)
    if req.is_active is not None:
        stmt = stmt.where(Neighborhood.is_active == req.is_active)
    if req.has_geometry is not None:
        stmt = stmt.where(
            Neighborhood.geom.is_not(None) if req.has_geometry else Neighborhood.geom.is_(None)
        )
    if req.search_term:
        nfkd = unicodedata.normalize("NFKD", req.search_term)
        term = "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()
        stmt = stmt.where(Neighborhood.search_name.contains(term, autoescape=True))
    return stmt


class SqlNeighborhoodAdminRepository(NeighborhoodAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self, *, req: ListNeighborhoodsAdminRequest) -> list[NeighborhoodAdminListItem]:
        geom = Neighborhood.geom
        bbox = case(
            (geom.is_(None), None),
            else_=array([ST_XMin(geom), ST_YMin(geom), ST_XMax(geom), ST_YMax(geom)]),
        )
        stmt = select(
            Neighborhood.id,
            Neighborhood.locality_id,
            Neighborhood.code,
            Neighborhood.name,
            Neighborhood.is_active,
            geom.is_not(None).label("has_geometry"),
            ST_AsSVG(ST_SimplifyPreserveTopology(geom, _SIMPLIFY_TOLERANCE), 1, 5).label("svg_path"),
            bbox.label("bbox"),
        )
        stmt = (
            _apply_filters(stmt, req)
            .order_by(Neighborhood.name, Neighborhood.id)
            .offset((req.page - 1) * req.page_size)
            .limit(req.page_size)
        )
        rows = self.session.exec(stmt).all()
        return [NeighborhoodAdminListItem.model_validate(row) for row in rows]

    def count_all(self, *, req: ListNeighborhoodsAdminRequest) -> int:
        stmt = _apply_filters(select(func.count()).select_from(Neighborhood), req)
        return self.session.exec(stmt).one()

    def get_coverage(self, *, req: ListNeighborhoodsAdminRequest) -> NeighborhoodCoverage:
        stmt = select(func.count(Neighborhood.geom), func.count()).select_from(Neighborhood)
        stmt = _apply_filters(stmt, req.model_copy(update={"has_geometry": None}))
        with_geometry, total = self.session.exec(stmt).one()
        return NeighborhoodCoverage(with_geometry=with_geometry, total=total)

    def get_by_id(self, *, neighborhood_id: uuid.UUID) -> Neighborhood | None:
        stmt = select(Neighborhood).where(Neighborhood.id == neighborhood_id)
        return self.session.exec(stmt).first()

    def get_detail(self, *, neighborhood_id: uuid.UUID) -> NeighborhoodAdminDetail | None:
        geom = Neighborhood.geom
        simplified = ST_SimplifyPreserveTopology(geom, _SIMPLIFY_TOLERANCE)
        stmt = select(
            Neighborhood.id,
            Neighborhood.locality_id,
            Neighborhood.code,
            Neighborhood.name,
            Neighborhood.postal_code,
            Neighborhood.latitude,
            Neighborhood.longitude,
            Neighborhood.is_active,
            cast(ST_AsGeoJSON(simplified, 6), JSON).label("geometry"),
            ST_Area(cast(geom, Geography)).label("area_m2"),
        ).where(Neighborhood.id == neighborhood_id)
        row = self.session.exec(stmt).first()
        return NeighborhoodAdminDetail.model_validate(row) if row else None

    def get_geometries(self, *, req: ListNeighborhoodGeometriesRequest) -> list[NeighborhoodGeometryItem]:
        bbox = ST_MakeEnvelope(*req.bbox, 4326)
        clipped = ST_SimplifyPreserveTopology(ST_ClipByBox2D(Neighborhood.geom, bbox), _SIMPLIFY_TOLERANCE)
        stmt = select(
            Neighborhood.id,
            Neighborhood.name,
            cast(ST_AsGeoJSON(clipped, 6), JSON).label("geometry"),
        ).where(
            ST_Intersects(Neighborhood.geom, bbox),
            Neighborhood.id != req.neighborhood_id,
        )
        rows = self.session.exec(stmt).all()
        return [NeighborhoodGeometryItem.model_validate(row) for row in rows]
    
    def get_many_by_search_names(self, *, locality_id: uuid.UUID, search_names: list[str]) -> list[Neighborhood]:
        stmt =  select(Neighborhood) \
                .where(Neighborhood.locality_id == locality_id) \
                .where(Neighborhood.search_name.in_(search_names))
        return self.session.exec(stmt).all()

    def bulk_insert(self, *, neighborhoods: list[Neighborhood]) -> None:
        stmt = insert(Neighborhood).values(
            [n.model_dump(exclude={"created_at", "updated_at"}) for n in neighborhoods]
        )
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
