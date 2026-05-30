from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

import redis
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = "postgresql+psycopg://kuli:kuli@localhost:5432/kuli"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "postgres"}


def main() -> int:
    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("DATABASE_URL", _env_file_value("DATABASE_URL") or DEFAULT_DATABASE_URL)
    os.environ.setdefault("REDIS_URL", _env_file_value("REDIS_URL") or DEFAULT_REDIS_URL)

    from app.core.config import get_settings
    from app.database import init_database

    settings = get_settings()
    _guard_local_database(settings.database_url)

    report: dict[str, object] = {
        "databaseUrl": _redact_url(settings.database_url),
        "redisUrl": _redact_url(settings.redis_url),
        "appEnv": settings.app_env,
        "checks": {},
    }

    engine = sa.create_engine(settings.database_url, pool_pre_ping=True)
    try:
        report["checks"]["postgresConnection"] = _wait_for_postgres(engine)
        report["checks"]["alembicUpgrade"] = _run_alembic_upgrade()
        report["checks"]["pgvector"] = _verify_pgvector(engine)
        report["checks"]["schema"] = _verify_schema(engine)
        report["checks"]["productionInit"] = _verify_production_init(init_database)
        report["checks"]["redis"] = _verify_redis(settings.redis_url)
    finally:
        engine.dispose()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _guard_local_database(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError(f"Production stack verification requires PostgreSQL, got {url.drivername}.")
    if url.host not in LOCAL_HOSTS and os.environ.get("ALLOW_NONLOCAL_PRODUCTION_VERIFY") != "true":
        raise RuntimeError(
            "Refusing to run migrations against a non-local database. "
            "Set ALLOW_NONLOCAL_PRODUCTION_VERIFY=true if this is intentional."
        )


def _env_file_value(key: str) -> str | None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() == key:
            return value.strip().strip("\"'")
    return None


def _redact_url(raw_url: str) -> str:
    url = make_url(raw_url)
    if url.password:
        url = url.set(password="***")
    return str(url)


def _wait_for_postgres(engine: sa.Engine) -> dict[str, object]:
    timeout = float(os.environ.get("VERIFY_TIMEOUT_SECONDS", "30"))
    started = time.monotonic()
    last_error = ""
    while time.monotonic() - started < timeout:
        try:
            with engine.connect() as connection:
                version = connection.execute(sa.text("select version()")).scalar_one()
                return {"ok": True, "version": version}
        except Exception as error:  # noqa: BLE001 - surfaced in verifier output
            last_error = str(error)
            time.sleep(1)
    raise RuntimeError(f"PostgreSQL did not become ready within {timeout:.0f}s: {last_error}")


def _run_alembic_upgrade() -> dict[str, object]:
    config = Config(str(ROOT / "apps/api/alembic.ini"))
    command.upgrade(config, "head")
    return {"ok": True, "revision": "head"}


def _verify_pgvector(engine: sa.Engine) -> dict[str, object]:
    with engine.begin() as connection:
        connection.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        version = connection.execute(sa.text("select extversion from pg_extension where extname = 'vector'")).scalar_one()
        dimensions = connection.execute(sa.text("select vector_dims('[1,2,3]'::vector)")).scalar_one()
    return {"ok": True, "extensionVersion": version, "sampleDimensions": dimensions}


def _verify_schema(engine: sa.Engine) -> dict[str, object]:
    required_tables = [
        "users",
        "service_categories",
        "orders",
        "order_events",
        "order_messages",
        "order_attachments",
        "quotes",
        "payment_records",
        "deliverables",
        "admin_audit_logs",
        "security_audit_logs",
        "notifications",
        "notification_events",
        "knowledge_embeddings",
        "agent_sessions",
        "order_automation_suggestions",
    ]
    with engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'public'
                """
            )
        ).scalars()
        present = set(rows)
    missing = [table for table in required_tables if table not in present]
    if missing:
        raise RuntimeError("Missing required tables: " + ", ".join(missing))
    return {"ok": True, "requiredTables": required_tables}


def _verify_production_init(init_database: object) -> dict[str, object]:
    init_database()
    return {"ok": True}


def _verify_redis(redis_url: str) -> dict[str, object]:
    client = redis.Redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3, decode_responses=True)
    key = f"kuli:production-stack:{uuid.uuid4()}"
    try:
        pong = client.ping()
        client.set(key, "ok", ex=30)
        value = client.get(key)
        if value != "ok":
            raise RuntimeError(f"Redis read-after-write failed: {value!r}")
        info = client.info(section="server")
        return {"ok": bool(pong), "version": info.get("redis_version")}
    finally:
        client.delete(key)
        client.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001 - CLI verifier should print one clear failure
        print(f"Production stack verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
