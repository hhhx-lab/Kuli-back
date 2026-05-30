from pathlib import Path
from typing import Any

import redis
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.entities import KnowledgeArticle, KnowledgeChunk, KnowledgeEmbedding

STRICT_ENVS = {"staging", "production"}


def dependency_report(db: Session, settings: Settings | None = None) -> dict[str, Any]:
    active_settings = settings or get_settings()
    dependencies = {
        "database": check_database(db, active_settings),
        "redis": check_redis(active_settings),
        "objectStorage": check_object_storage(active_settings),
        "mail": check_mail(active_settings),
        "llm": check_llm(active_settings),
        "rag": check_rag(db),
    }
    return {
        "ok": all(item["ok"] or not item["required"] for item in dependencies.values()),
        "service": "kuli-api",
        "version": "0.2.0",
        "environment": active_settings.app_env,
        "dependencies": dependencies,
    }


def is_strict_env(settings: Settings) -> bool:
    return settings.app_env in STRICT_ENVS


def check_database(db: Session, settings: Settings) -> dict[str, Any]:
    try:
        db.execute(text("select 1")).scalar_one()
        bind = db.get_bind()
        url = bind.url if bind is not None else make_url(settings.database_url)
        return {
            "ok": True,
            "required": True,
            "status": "ok",
            "driver": url.get_backend_name(),
            "detail": "database query succeeded",
        }
    except Exception as error:  # noqa: BLE001 - surfaced as health detail
        return {"ok": False, "required": True, "status": "unreachable", "driver": "unknown", "detail": str(error)}


def check_redis(settings: Settings) -> dict[str, Any]:
    required = is_strict_env(settings)
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25, decode_responses=True)
        pong = client.ping()
        client.close()
        return {"ok": bool(pong), "required": required, "status": "ok", "detail": "redis ping succeeded"}
    except Exception as error:  # noqa: BLE001 - dependency health should not raise
        return {"ok": False, "required": required, "status": "unreachable", "detail": str(error)}


def check_object_storage(settings: Settings) -> dict[str, Any]:
    required = is_strict_env(settings)
    provider = settings.object_storage_provider
    if provider == "local":
        root = Path(settings.object_storage_local_dir)
        return {
            "ok": True,
            "required": False,
            "status": "local",
            "provider": provider,
            "detail": str(root),
        }
    if provider in {"s3", "r2", "oss"}:
        has_credentials = bool(settings.object_storage_bucket and settings.object_storage_access_key_id and settings.object_storage_secret_access_key)
        return {
            "ok": has_credentials,
            "required": required,
            "status": "configured" if has_credentials else "missing-credentials",
            "provider": provider,
            "detail": settings.object_storage_bucket,
        }
    return {"ok": False, "required": required, "status": "unsupported", "provider": provider, "detail": "unsupported provider"}


def check_mail(settings: Settings) -> dict[str, Any]:
    required = is_strict_env(settings)
    if not settings.mail_provider:
        return {"ok": False, "required": required, "status": "disabled", "provider": "", "detail": "MAIL_PROVIDER is empty"}
    if settings.mail_provider == "smtp":
        configured = bool(settings.mail_from and settings.smtp_host and settings.smtp_username and settings.smtp_password)
        return {
            "ok": configured,
            "required": required,
            "status": "configured" if configured else "missing-credentials",
            "provider": settings.mail_provider,
            "detail": settings.smtp_host,
        }
    return {
        "ok": True,
        "required": required,
        "status": "configured",
        "provider": settings.mail_provider,
        "detail": "notification provider configured",
    }


def check_llm(settings: Settings) -> dict[str, Any]:
    strict = is_strict_env(settings)
    provider = settings.effective_llm_provider
    model = settings.effective_llm_model
    if provider == "local-rules" or model == "local-rules":
        return {
            "ok": True,
            "required": False,
            "status": "local-rules",
            "provider": provider,
            "model": model,
            "detail": "agent can fall back to local rules",
        }
    configured = bool(settings.effective_llm_api_key and model)
    return {
        "ok": configured,
        "required": strict,
        "status": "configured" if configured else "missing-key",
        "provider": provider,
        "model": model,
        "detail": "remote LLM configured" if configured else "OPENAI_API_KEY/LLM_API_KEY or model is missing",
    }


def check_rag(db: Session) -> dict[str, Any]:
    article_count = db.query(KnowledgeArticle).count()
    chunk_count = db.query(KnowledgeChunk).count()
    embedding_count = db.query(KnowledgeEmbedding).count()
    status = "remote-rag" if embedding_count and chunk_count else "local-rules-fallback"
    return {
        "ok": article_count > 0,
        "required": True,
        "status": status,
        "articleCount": article_count,
        "chunkCount": chunk_count,
        "embeddingCount": embedding_count,
        "detail": "knowledge base has indexed chunks" if chunk_count else "seeded knowledge articles available",
    }
