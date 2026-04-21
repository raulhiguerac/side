from collections.abc import Generator

from sqlmodel import Session

from app.db import get_session as _get_session


def get_session() -> Generator[Session, None, None]:
    yield from _get_session()
