from typing import Protocol

from app.services.search.ports.property_search_repository import PropertySearchRepository


class SearchUnitOfWork(Protocol):
    properties: PropertySearchRepository
