import uuid

from sqlalchemy import Select, func
from sqlmodel import Session, select

from app.models.location import Locality
from app.services.catalog_admin.ports.locality_repository import LocalityAdminRepository
from app.services.catalog_admin.schemas.locality import GetAllLocalitiesRequest


def _apply_filters(stmt: Select, filters: GetAllLocalitiesRequest) -> Select:
    if filters.country_id:
        stmt = stmt.where(Locality.country_id == filters.country_id)
    if filters.admin_division_id:
        stmt = stmt.where(Locality.admin_division_id == filters.admin_division_id)
    if filters.is_active is not None:
        stmt = stmt.where(Locality.is_active == filters.is_active)
    return stmt


class SqlLocalityAdminRepository(LocalityAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self, *, filters: GetAllLocalitiesRequest) -> list[Locality]:
        stmt = (
            _apply_filters(select(Locality), filters)
            .order_by(Locality.name, Locality.id)
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        return list(self.session.exec(stmt).all())

    def count_all(self, *, filters: GetAllLocalitiesRequest) -> int:
        stmt = _apply_filters(select(func.count()).select_from(Locality), filters)
        return self.session.exec(stmt).one()

    def get_by_id(self, *, locality_id: uuid.UUID) -> Locality | None:
        stmt = select(Locality).where(Locality.id == locality_id)
        return self.session.exec(stmt).first()

    def add(self, *, locality: Locality) -> Locality:
        self.session.add(locality)
        self.session.flush()
        return locality
