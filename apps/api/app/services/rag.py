from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.entities import KnowledgeArticle, KnowledgeChunk, KnowledgeEmbedding
from app.services.embeddings import cosine_similarity, embed_text, vector_from_json, vector_to_pg_literal


def _terms(query: str) -> list[str]:
    ascii_terms = re.findall(r"[a-zA-Z0-9_\\-]{2,}", query.lower())
    chinese_terms = [query[i : i + 2] for i in range(max(len(query) - 1, 0)) if re.search(r"[\u4e00-\u9fff]", query[i : i + 2])]
    return list(dict.fromkeys([*ascii_terms, *chinese_terms]))


def search_knowledge(db: Session, query: str, limit: int = 4) -> list[KnowledgeArticle]:
    lexical_rows = _lexical_search(db, query, limit)
    semantic_rows = _semantic_search(db, query, limit)
    return _merge_results([*lexical_rows, *semantic_rows], limit)


@dataclass(frozen=True)
class KnowledgeHit:
    article: KnowledgeArticle
    chunk: KnowledgeChunk
    score: int


def search_knowledge_hits(db: Session, query: str, limit: int = 5) -> list[KnowledgeHit]:
    terms = _terms(query)
    rows = db.query(KnowledgeArticle, KnowledgeChunk).join(KnowledgeChunk, KnowledgeChunk.article_id == KnowledgeArticle.id).all()
    scored: list[KnowledgeHit] = []
    for article, chunk in rows:
        haystack = f"{article.title}\n{article.body}\n{article.tags}\n{chunk.section}\n{chunk.content}".lower()
        score = 0
        lowered_query = query.lower().strip()
        if lowered_query and lowered_query in haystack:
            score += 12
        for term in terms:
            if term in haystack:
                score += 2
            if term and term in article.title.lower():
                score += 3
            if term and term in chunk.section.lower():
                score += 3
        if article.source.startswith("doc:"):
            score += 1
        if score:
            scored.append(KnowledgeHit(article=article, chunk=chunk, score=score + chunk.priority))
    scored.sort(key=lambda item: item.score, reverse=True)
    return _dedupe_hits(scored, limit)


def _semantic_search(db: Session, query: str, limit: int) -> list[KnowledgeArticle]:
    query_vector = embed_text(query, allow_remote=False).vector
    if not query_vector:
        return []
    if db.bind and db.bind.dialect.name == "postgresql":
        return _postgres_vector_search(db, query_vector, limit)
    return _python_vector_search(db, query_vector, limit)


def _postgres_vector_search(db: Session, query_vector: list[float], limit: int) -> list[KnowledgeArticle]:
    rows = db.execute(
        text(
            """
            SELECT knowledge_articles.id
            FROM knowledge_articles
            JOIN knowledge_chunks ON knowledge_chunks.article_id = knowledge_articles.id
            JOIN knowledge_embeddings ON knowledge_embeddings.chunk_id = knowledge_chunks.id
            WHERE knowledge_embeddings.embedding_vector IS NOT NULL
            ORDER BY knowledge_embeddings.embedding_vector <=> CAST(:query_vector AS vector)
            LIMIT :limit
            """
        ),
        {"query_vector": vector_to_pg_literal(query_vector), "limit": limit},
    ).all()
    ids = [row[0] for row in rows]
    if not ids:
        return []
    article_map = {item.id: item for item in db.query(KnowledgeArticle).filter(KnowledgeArticle.id.in_(ids)).all()}
    return [article_map[item_id] for item_id in ids if item_id in article_map]


def _python_vector_search(db: Session, query_vector: list[float], limit: int) -> list[KnowledgeArticle]:
    rows = (
        db.query(KnowledgeArticle, KnowledgeEmbedding.embedding_json)
        .join(KnowledgeChunk, KnowledgeChunk.article_id == KnowledgeArticle.id)
        .join(KnowledgeEmbedding, KnowledgeEmbedding.chunk_id == KnowledgeChunk.id)
        .filter(KnowledgeEmbedding.embedding_json != "[]")
        .all()
    )
    scored: list[tuple[float, KnowledgeArticle]] = []
    for article, raw_vector in rows:
        score = cosine_similarity(query_vector, vector_from_json(raw_vector))
        if score > 0:
            scored.append((score, article))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]


def _lexical_search(db: Session, query: str, limit: int) -> list[KnowledgeArticle]:
    rows = db.query(KnowledgeArticle).all()
    terms = _terms(query)
    scored: list[tuple[int, KnowledgeArticle]] = []
    for row in rows:
        haystack = f"{row.title}\n{row.body}\n{row.tags}".lower()
        score = 0
        if query and query in row.body:
            score += 8
        for term in terms:
            if term in haystack:
                score += 1
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored[:limit]]


def _merge_results(rows: list[KnowledgeArticle], limit: int) -> list[KnowledgeArticle]:
    merged: list[KnowledgeArticle] = []
    seen: set[str] = set()
    for row in rows:
        if row.id in seen:
            continue
        merged.append(row)
        seen.add(row.id)
        if len(merged) >= limit:
            break
    return merged


def _dedupe_hits(rows: list[KnowledgeHit], limit: int) -> list[KnowledgeHit]:
    merged: list[KnowledgeHit] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.article.source, row.chunk.anchor)
        if key in seen:
            continue
        merged.append(row)
        seen.add(key)
        if len(merged) >= limit:
            break
    return merged
