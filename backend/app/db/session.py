from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base

engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _migrate_sqlite() -> None:
    """Add new columns on existing SQLite DB without wiping data."""
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(deploy_jobs)")).fetchall()
        if not rows:
            return
        names = {row[1] for row in rows}
        if "phase" not in names:
            conn.execute(text("ALTER TABLE deploy_jobs ADD COLUMN phase VARCHAR(32) DEFAULT 'pending'"))
        if "progress" not in names:
            conn.execute(text("ALTER TABLE deploy_jobs ADD COLUMN progress INTEGER DEFAULT 0"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
