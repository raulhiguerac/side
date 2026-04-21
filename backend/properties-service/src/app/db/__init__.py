from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config.settings import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"options": "-c timezone=utc"})


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
