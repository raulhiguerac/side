from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.models.location import FetchZone
from app.services.geo_resolution.ports.fetch_zone_repository import FetchZoneRepository


class SqlFetchZoneRepository(FetchZoneRepository):

    def __init__(self, session: Session):
        self.session = session

    def get_by_h3_index(self, *, h3_index: str) -> FetchZone | None:
        stmt = select(FetchZone).where(FetchZone.h3_index == h3_index)
        return self.session.exec(stmt).first()

    def add_or_update(self, *, fetch_zone: FetchZone) -> None:
        stmt = insert(FetchZone).values(fetch_zone.model_dump())
        stmt = stmt.on_conflict_do_update(
            index_elements=["h3_index"],
            set_={
                    k: stmt.excluded[k] for k in inspect(FetchZone) \
                    .columns.keys() if k not in {"id", "created_at", "h3_index"}
                },
        )
        self.session.execute(stmt)
        self.session.flush()
