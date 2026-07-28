from sqlmodel import Session

from app.services.search.adapters.sql_property_search_repository import SqlPropertySearchRepository
from app.services.search.ports.unit_of_work import SearchUnitOfWork


class SqlSearchUnitOfWork(SearchUnitOfWork):
    def __init__(self, session: Session) -> None:
        self.properties = SqlPropertySearchRepository(session=session)
