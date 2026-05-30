from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app import database
from app.database import init_database
from app.models.entities import KnowledgeArticle, KnowledgeChunk, KnowledgeEmbedding, now_iso
from app.services.docs import DocPage, load_docs
from app.services.knowledge import ensure_chunk_embedding


HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)(?:\s+\{#([a-z0-9-]+)\})?\s*$")


def index_knowledge(root: str | Path | None = None) -> dict[str, int]:
    docs = load_docs(root)

    article_count = 0
    chunk_count = 0
    embedding_count = 0
    with database.SessionLocal() as db:
        for doc in docs:
            article = _upsert_doc_article(db, doc)
            chunks = _replace_doc_chunks(db, article, doc)
            article_count += 1
            chunk_count += len(chunks)
            for chunk in chunks:
                if ensure_chunk_embedding(db, chunk, allow_remote=True, force=True):
                    embedding_count += 1
        db.commit()
    return {"articles": article_count, "chunks": chunk_count, "embeddings": embedding_count}


def _upsert_doc_article(db: database.Session, doc: DocPage) -> KnowledgeArticle:
    source = f"doc:{doc.slug}"
    tags_json = json.dumps(doc.tags, ensure_ascii=False)
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.source == source).first()
    if article:
        article.scope = "docs"
        article.title = doc.title
        article.body = doc.content
        article.tags = tags_json
        article.updated_at = now_iso()
    else:
        article = KnowledgeArticle(scope="docs", title=doc.title, body=doc.content, tags=tags_json, source=source)
        db.add(article)
        db.flush()
    return article


def _replace_doc_chunks(db: database.Session, article: KnowledgeArticle, doc: DocPage) -> list[KnowledgeChunk]:
    old_chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.article_id == article.id).all()
    old_ids = [chunk.id for chunk in old_chunks]
    if old_ids:
        db.query(KnowledgeEmbedding).filter(KnowledgeEmbedding.chunk_id.in_(old_ids)).delete(synchronize_session=False)
    for chunk in old_chunks:
        db.delete(chunk)
    db.flush()

    source_path = doc.source_path
    chunks: list[KnowledgeChunk] = []
    for index, item in enumerate(_chunk_doc(doc), start=0):
        chunk = KnowledgeChunk(
            article_id=article.id,
            chunk_index=index,
            slug=doc.slug,
            source_path=source_path,
            section=str(item["section"]),
            anchor=str(item["anchor"]),
            priority=int(item["priority"]),
            content=str(item["content"]),
            token_count=len(str(item["content"])),
        )
        db.add(chunk)
        chunks.append(chunk)
    db.flush()
    return chunks


def _chunk_doc(doc: DocPage) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_section = doc.title
    current_anchor = doc.slug
    buffer: list[str] = []

    def emit() -> None:
        nonlocal buffer
        content = "\n".join(line for line in buffer if line.strip()).strip()
        if not content:
            buffer = []
            return
        chunks.append(
            {
                "section": current_section,
                "anchor": current_anchor,
                "priority": max(1, 100 - len(chunks)),
                "content": f"{doc.title}\n{current_section}\n{content}",
            }
        )
        buffer = []

    for raw_line in doc.content.splitlines():
        heading = HEADING_RE.match(raw_line.strip())
        if heading:
            emit()
            _, title, explicit_anchor = heading.groups()
            current_section = title.strip()
            current_anchor = explicit_anchor or _slugify(current_section)
            buffer.append(current_section)
            continue
        buffer.append(raw_line)
    emit()

    if not chunks:
        chunks.append({"section": doc.title, "anchor": doc.slug, "priority": 1, "content": doc.content})
    return chunks


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def main() -> None:
    init_database()
    result = index_knowledge()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
