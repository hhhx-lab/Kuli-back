from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entities import KnowledgeChunk, KnowledgeEmbedding
from app.services.knowledge import ensure_chunk_embedding
from app.tasks.celery_app import celery_app


@celery_app.task(name="knowledge.embed_missing_chunks")
def embed_missing_chunks() -> int:
    with SessionLocal() as db:
        return embed_missing_chunks_sync(db)


def embed_missing_chunks_sync(db: Session) -> int:
    count = 0
    chunks = db.query(KnowledgeChunk).all()
    for chunk in chunks:
        embedding = db.query(KnowledgeEmbedding).filter(KnowledgeEmbedding.chunk_id == chunk.id).first()
        needs_embedding = (
            not embedding
            or not embedding.embedding_json
            or embedding.embedding_json == "[]"
            or not embedding.embedding_vector
            or embedding.provider == "pending"
        )
        if needs_embedding and ensure_chunk_embedding(db, chunk, allow_remote=True, force=True):
            count += 1
    db.commit()
    return count
