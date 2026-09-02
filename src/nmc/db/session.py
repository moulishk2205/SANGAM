"""
Engine, session factory, and the one place the database URL is decided.

`DATABASE_URL` overrides; the default is a SQLite file beside the repo. SQLite
is chosen so the demo starts with one command and runs with the network off —
see the note at the top of models.py. Nothing in the schema is SQLite-specific.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "sangam.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_PATH}")

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine: Engine = create_engine(
    DATABASE_URL,
    # SQLite's default is one connection per thread; FastAPI runs sync endpoints
    # in a threadpool, so that guard has to be lifted or every request after the
    # first raises. Safe here because SQLAlchemy pools per-connection.
    connect_args={"check_same_thread": False} if _IS_SQLITE else {},
    # Postgres benefits from a real pool; SQLite ignores these.
    pool_pre_ping=True,
    future=True,
)


if _IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        """
        Two pragmas that matter and are off by default.

        WAL lets a reader and a writer coexist, which a web app needs the moment
        two requests overlap. Foreign keys are *not enforced* in SQLite unless
        asked — the schema would declare relationships the database quietly
        ignored, and an orphaned mapping is exactly the kind of corruption an
        audit trail must not permit.
        """
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False,
                            class_=Session, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency. Commits on success, rolls back on any exception."""
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def describe() -> dict:
    """What the health endpoint reports about storage."""
    return {
        "backend": "sqlite" if _IS_SQLITE else engine.dialect.name,
        "url": DATABASE_URL if not _IS_SQLITE else f"sqlite:///{DEFAULT_PATH.name}",
        "path": str(DEFAULT_PATH) if _IS_SQLITE else "",
    }
