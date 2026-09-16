from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
if settings.is_sqlite:
    Path("./storage").mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)

if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
