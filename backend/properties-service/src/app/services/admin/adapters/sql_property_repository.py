import uuid

from sqlmodel import Session, select

from app.models.property import Property


class SqlAdminPropertyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, property_id: uuid.UUID) -> Property | None:
        stmt = select(Property).where(Property.id == property_id)
        return self.session.exec(stmt).first()
