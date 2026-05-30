from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app import database
from app.core.config import get_settings
from app.database import init_database
from app.models.entities import KnowledgeChunk, KnowledgeEmbedding
from app.services.docs import REQUIRED_DOC_SLUGS, REQUIRED_FRONTMATTER, VALID_DOC_STATUSES, _parse_frontmatter, docs_root
from app.services.embeddings import remote_embeddings_enabled


def run_doctor(root: str | Path | None = None) -> dict[str, Any]:
    settings = get_settings()
    active_root = Path(root) if root is not None else docs_root()
    missing = [slug for slug in REQUIRED_DOC_SLUGS if not (active_root / f"{slug}.md").exists()]

    frontmatter_ok = 0
    duplicate_slugs: list[str] = []
    invalid_status: list[str] = []
    missing_required: dict[str, list[str]] = {}
    statuses: dict[str, int] = {}
    seen: set[str] = set()
    empty_docs: list[str] = []
    if not missing:
        for slug in REQUIRED_DOC_SLUGS:
            path = active_root / f"{slug}.md"
            meta, content = _parse_frontmatter(path.read_text(encoding="utf-8"))
            doc_slug = str(meta.get("slug", ""))
            required_missing = [field for field in REQUIRED_FRONTMATTER if field not in meta or _is_empty_frontmatter_value(meta[field])]
            if required_missing:
                missing_required[doc_slug or slug] = required_missing
            status = str(meta.get("status", ""))
            if status:
                statuses[status] = statuses.get(status, 0) + 1
            if status not in VALID_DOC_STATUSES:
                invalid_status.append(doc_slug or slug)
            if not required_missing and status in VALID_DOC_STATUSES:
                frontmatter_ok += 1
            if doc_slug in seen:
                duplicate_slugs.append(doc_slug)
            seen.add(doc_slug)
            if not content.strip():
                empty_docs.append(doc_slug or slug)

    with database.SessionLocal() as db:
        chunks = db.query(KnowledgeChunk).all()
        embeddings = db.query(KnowledgeEmbedding).all()
        embedding_dimensions = {item.vector_dimension for item in embeddings if item.embedding_json != "[]"}

    mode = _mode()
    ok = not missing and not duplicate_slugs and not empty_docs and not missing_required and not invalid_status and len(chunks) >= len(REQUIRED_DOC_SLUGS)
    return {
        "ok": ok,
        "mode": mode,
        "requiredDocs": {"expected": REQUIRED_DOC_SLUGS, "missing": missing},
        "frontmatter": {
            "ok": frontmatter_ok,
            "duplicates": duplicate_slugs,
            "empty": empty_docs,
            "missingRequired": missing_required,
            "invalidStatus": invalid_status,
            "statuses": statuses,
        },
        "chunks": {"total": len(chunks), "minimum": len(REQUIRED_DOC_SLUGS)},
        "embeddings": {
            "total": len(embeddings),
            "dimension": max(embedding_dimensions) if embedding_dimensions else int(settings.vector_dimension),
            "expectedDimension": int(settings.vector_dimension),
        },
        "env": {
            "OPENAI_API_KEY": bool(settings.llm_api_key),
            "OPENAI_MODEL": bool(settings.llm_model),
            "EMBEDDING_MODEL": bool(settings.embedding_model),
            "KNOWLEDGE_ROOT": str(active_root),
        },
    }


def _mode() -> str:
    settings = get_settings()
    if remote_embeddings_enabled() and settings.llm_model != "local-rules":
        return "remote-rag"
    if settings.llm_provider != "local-rules" and settings.llm_model != "local-rules":
        return "local-rag"
    return "local-rules-fallback"


def _is_empty_frontmatter_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


def main() -> None:
    init_database()
    report = run_doctor()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
