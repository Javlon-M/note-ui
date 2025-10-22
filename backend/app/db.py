from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import SQLModel, create_engine, Session

from .core.config import settings

engine = create_engine(settings.database_url, echo=False, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
