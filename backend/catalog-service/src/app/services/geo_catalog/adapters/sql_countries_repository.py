from typing import List

from sqlmodel import Session, select

from app.models.location import Country
from app.services.geo_catalog.ports.countries_repository import CountryRepository


class SqlCountryRepository(CountryRepository):
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_countries(
            self, 
        ) -> List[Country]:

        stmt = (
            select(Country)
            .where(Country.is_active == True)
            .order_by(Country.name)
        )

        return self.session.exec(stmt).all()