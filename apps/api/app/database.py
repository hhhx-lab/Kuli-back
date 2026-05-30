from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_sqlite_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    path = database_url.removeprefix("sqlite:///")
    if path and path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(get_settings().database_url)
engine = create_engine(get_settings().database_url, connect_args=_connect_args(get_settings().database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def configure_database(database_url: str) -> None:
    global engine, SessionLocal
    _ensure_sqlite_dir(database_url)
    engine = create_engine(database_url, connect_args=_connect_args(database_url))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_database() -> None:
    from app.models.entities import seed_database
    from app.services.security_controls import reset_security_rate_limits

    settings = get_settings()
    reset_security_rate_limits()
    _ensure_postgres_extensions(engine)
    if settings.app_env in {"local", "dev", "development", "test"}:
        Base.metadata.create_all(bind=engine)
        _ensure_local_schema_compat(engine)
    elif not _has_required_schema(engine):
        raise RuntimeError("Database schema is missing. Run Alembic migrations before starting the API.")
    with SessionLocal() as db:
        seed_database(db)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_postgres_extensions(active_engine: Engine) -> None:
    if active_engine.dialect.name != "postgresql":
        return
    with active_engine.begin() as connection:
        connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")


def _has_required_schema(active_engine: Engine) -> bool:
    inspector = inspect(active_engine)
    return inspector.has_table("users") and inspector.has_table("orders") and inspector.has_table("alembic_version")


def _ensure_local_schema_compat(active_engine: Engine) -> None:
    if active_engine.dialect.name != "sqlite":
        return
    inspector = inspect(active_engine)
    with active_engine.begin() as connection:
        if inspector.has_table("knowledge_embeddings"):
            columns = {column["name"] for column in inspector.get_columns("knowledge_embeddings")}
            if "embedding_vector" not in columns:
                connection.exec_driver_sql("ALTER TABLE knowledge_embeddings ADD COLUMN embedding_vector TEXT")
        if inspector.has_table("knowledge_chunks"):
            columns = {column["name"] for column in inspector.get_columns("knowledge_chunks")}
            for name, ddl in {
                "slug": "VARCHAR(120) NOT NULL DEFAULT ''",
                "source_path": "TEXT NOT NULL DEFAULT ''",
                "section": "VARCHAR(200) NOT NULL DEFAULT ''",
                "anchor": "VARCHAR(160) NOT NULL DEFAULT ''",
                "priority": "INTEGER NOT NULL DEFAULT 0",
            }.items():
                if name not in columns:
                    connection.exec_driver_sql(f"ALTER TABLE knowledge_chunks ADD COLUMN {name} {ddl}")
        if inspector.has_table("order_attachments"):
            columns = {column["name"] for column in inspector.get_columns("order_attachments")}
            for name, ddl in {
                "parsed_summary": "TEXT NOT NULL DEFAULT ''",
                "scan_error": "TEXT NOT NULL DEFAULT ''",
                "retry_count": "INTEGER NOT NULL DEFAULT 0",
                "last_scanned_at": "VARCHAR(64)",
            }.items():
                if name not in columns:
                    connection.exec_driver_sql(f"ALTER TABLE order_attachments ADD COLUMN {name} {ddl}")
        if inspector.has_table("users"):
            columns = {column["name"] for column in inspector.get_columns("users")}
            for name, ddl in {
                "points": "INTEGER NOT NULL DEFAULT 0",
                "referral_code": "VARCHAR(40) NOT NULL DEFAULT ''",
                "referred_by_user_id": "VARCHAR(64)",
                "email_verified_at": "VARCHAR(64)",
                "failed_login_count": "INTEGER NOT NULL DEFAULT 0",
                "locked_until": "VARCHAR(64)",
            }.items():
                if name not in columns:
                    connection.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {name} {ddl}")
        if inspector.has_table("notification_events"):
            columns = {column["name"] for column in inspector.get_columns("notification_events")}
            for name, ddl in {
                "event_type": "VARCHAR(80) NOT NULL DEFAULT 'system'",
                "user_id": "VARCHAR(64)",
                "notification_id": "VARCHAR(64)",
                "retry_count": "INTEGER NOT NULL DEFAULT 0",
                "last_error": "TEXT NOT NULL DEFAULT ''",
                "idempotency_key": "VARCHAR(220) NOT NULL DEFAULT ''",
                "updated_at": "VARCHAR(64) NOT NULL DEFAULT ''",
            }.items():
                if name not in columns:
                    connection.exec_driver_sql(f"ALTER TABLE notification_events ADD COLUMN {name} {ddl}")
