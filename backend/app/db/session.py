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


def _table_cols(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def _migrate_sqlite() -> None:
    with engine.begin() as conn:
        # deploy_jobs
        cols = _table_cols(conn, "deploy_jobs")
        if cols:
            if "phase" not in cols:
                conn.execute(text("ALTER TABLE deploy_jobs ADD COLUMN phase VARCHAR(32) DEFAULT 'pending'"))
            if "progress" not in cols:
                conn.execute(text("ALTER TABLE deploy_jobs ADD COLUMN progress INTEGER DEFAULT 0"))
            if "created_by" not in cols:
                conn.execute(text("ALTER TABLE deploy_jobs ADD COLUMN created_by INTEGER"))

        # clusters
        cols = _table_cols(conn, "clusters")
        if cols and "owner_id" not in cols:
            conn.execute(text("ALTER TABLE clusters ADD COLUMN owner_id INTEGER"))

        # users
        cols = _table_cols(conn, "users")
        if cols:
            if "display_name" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN display_name VARCHAR(64) DEFAULT ''"))
            if "enabled" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN enabled BOOLEAN DEFAULT 1"))
            if "department" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(128) DEFAULT ''"))
            if "title" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN title VARCHAR(64) DEFAULT ''"))
            if "manager_id" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN manager_id INTEGER"))

        # hosts：SSH 凭据与 Agent 状态
        cols = _table_cols(conn, "hosts")
        if cols:
            if "ssh_password_enc" not in cols:
                conn.execute(text("ALTER TABLE hosts ADD COLUMN ssh_password_enc TEXT DEFAULT ''"))
            if "agent_status" not in cols:
                conn.execute(text("ALTER TABLE hosts ADD COLUMN agent_status VARCHAR(32) DEFAULT 'unverified'"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
