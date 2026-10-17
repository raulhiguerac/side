import uuid

from sqlalchemy import Select, func
from sqlmodel import Session, select

from app.models.location import Country
from app.services.catalog_admin.ports.country_repository import CountryAdminRepository
from app.services.catalog_admin.schemas.country import GetAllCountriesRequest


def _apply_filters(stmt: Select, filters: GetAllCountriesRequest) -> Select:
    if filters.is_active is not None:
        stmt = stmt.where(Country.is_active == filters.is_active)
    if filters.is_supported is not None:
        stmt = stmt.where(Country.is_supported == filters.is_supported)
    return stmt


class SqlCountryRepository(CountryAdminRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self, *, filters: GetAllCountriesRequest) -> list[Country]:
        stmt = (
            _apply_filters(select(Country), filters)
            .order_by(Country.name, Country.id)
            .offset(filters.offset)
            .limit(filters.page_size)
        )
        return list(self.session.exec(stmt).all())

    def count_all(self, *, filters: GetAllCountriesRequest) -> int:
        stmt = _apply_filters(select(func.count()).select_from(Country), filters)
        return self.session.exec(stmt).one()

    def get_by_id(self, *, country_id: uuid.UUID) -> Country | None:
        stmt = select(Country).where(Country.id == country_id)
        return self.session.exec(stmt).first()

    def add(self, *, country: Country) -> Country:
        self.session.add(country)
        self.session.flush()
        return country
