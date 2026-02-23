import uuid
from typing import Optional

from sqlmodel import Session, select

from app.models.location import Country
from app.services.catalog_admin.ports.country_repository import CountryAdminRepository


class SqlCountryRepository(CountryAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, *, country_id: uuid.UUID) -> Optional[Country]:
        stmt = select(Country).where(Country.id == country_id)
        return self.session.exec(stmt).first()

    def add(self, *, country: Country) -> Country:
        self.session.add(country)
        self.session.flush()
        return country
