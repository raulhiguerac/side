import uuid
from typing import Optional

from sqlmodel import select, Session

from app.models.location import AdminDivision
from app.services.catalog_admin.ports.admin_division_repository import AdminDivisionAdminRepository


class SqlAdminDivisionRepository(AdminDivisionAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, admin_division_id: uuid.UUID) -> Optional[AdminDivision]:
        stmt = select(AdminDivision).where(AdminDivision.id == admin_division_id)
        return self.session.exec(stmt).first()

    def add(self, *, admin_division: AdminDivision) -> AdminDivision:
        self.session.add(admin_division)
        self.session.flush()
        return admin_division
