import os

from collections.abc import Generator

from sqlmodel import Session, create_engine

database_URL = os.getenv('DATABASE_CATALOG_URL')

engine = create_engine(database_URL, connect_args={"options": "-c timezone=utc"})

def get_session() -> Generator[Session,None,None]:
    with Session(engine) as session:
        yield session