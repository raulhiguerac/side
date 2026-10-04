from fastapi import Depends
from sqlmodel import Session

from app.api.deps.db import get_session
from app.services.catalog_admin.adapters.sql_unit_of_work import (
    SqlCatalogAdminUnitOfWork,
)
from app.services.catalog_admin.ports.unit_of_work import CatalogAdminUnitOfWork


def get_uow(session: Session = Depends(get_session)) -> CatalogAdminUnitOfWork:
    return SqlCatalogAdminUnitOfWork(session=session)
