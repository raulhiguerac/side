import uuid
from typing import Optional

from sqlalchemy import Select, func
from sqlmodel import Session, select

from app.models.location import AdminDivision
from app.services.catalog_admin.ports.admin_division_repository import (
    AdminDivisionAdminRepository,
)
from app.services.catalog_admin.schemas.admin_division import (
    GetAllAdminDivisionsRequest,
)


def _apply_filters(stmt: Select, filters: GetAllAdminDivisionsRequest) -> Select:
    if filters.country_id:
        stmt = stmt.where(AdminDivision.country_id == filters.country_id)
    if filters.is_active is not None:
        stmt = stmt.where(AdminDivision.is_active == filters.is_active)
    return stmt


class SqlAdminDivisionRepository(AdminDivisionAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self, *, filters: GetAllAdminDivisionsRequest) -> list[AdminDivision]:
        stmt = (
            _apply_filters(select(AdminDivision), filters)
            .order_by(AdminDivision.name, AdminDivision.id)
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        return list(self.session.exec(stmt).all())

    def count_all(self, *, filters: GetAllAdminDivisionsRequest) -> int:
        stmt = _apply_filters(select(func.count()).select_from(AdminDivision), filters)
        return self.session.exec(stmt).one()

    def get_by_id(self, *, admin_division_id: uuid.UUID) -> Optional[AdminDivision]:
        stmt = select(AdminDivision).where(AdminDivision.id == admin_division_id)
        return self.session.exec(stmt).first()

    def add(self, *, admin_division: AdminDivision) -> AdminDivision:
        self.session.add(admin_division)
        self.session.flush()
        return admin_division
