from pathlib import Path
import sys

from app import database
from app.database import configure_database, init_database
from app.models.entities import KnowledgeArticle, KnowledgeChunk, KnowledgeEmbedding


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_index_knowledge_upserts_docs_with_chunk_metadata(tmp_path: Path) -> None:
    from scripts.index_knowledge import index_knowledge

    configure_database(f"sqlite:///{tmp_path / 'index.db'}")
    init_database()

    result = index_knowledge()
    assert result["articles"] == 5
    assert result["chunks"] >= 5

    with database.SessionLocal() as db:
      article = db.query(KnowledgeArticle).filter(KnowledgeArticle.source == "doc:quick-start").one()
      assert article.scope == "docs"
      assert article.title == "快速开始"

      chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.article_id == article.id).order_by(KnowledgeChunk.chunk_index).all()
      assert chunks
      assert chunks[0].slug == "quick-start"
      assert chunks[0].source_path.endswith("apps/api/knowledge/docs/quick-start.md")
      assert chunks[0].section
      assert chunks[0].anchor
      assert chunks[0].priority >= 1
      assert "写小纸条" in "\n".join(chunk.content for chunk in chunks)

      embeddings = db.query(KnowledgeEmbedding).join(KnowledgeChunk, KnowledgeEmbedding.chunk_id == KnowledgeChunk.id).filter(KnowledgeChunk.slug == "quick-start").all()
      assert embeddings
      assert all(item.embedding_json != "[]" for item in embeddings)

    again = index_knowledge()
    assert again["articles"] == 5
    with database.SessionLocal() as db:
      assert db.query(KnowledgeArticle).filter(KnowledgeArticle.source.like("doc:%")).count() == 5


def test_knowledge_doctor_reports_required_docs_and_fallback_mode(tmp_path: Path) -> None:
    from scripts.index_knowledge import index_knowledge
    from scripts.knowledge_doctor import run_doctor

    configure_database(f"sqlite:///{tmp_path / 'doctor.db'}")
    init_database()
    index_knowledge()

    report = run_doctor()
    assert report["ok"] is True
    assert report["mode"] == "local-rules-fallback"
    assert report["requiredDocs"]["missing"] == []
    assert report["frontmatter"]["ok"] == 5
    assert report["frontmatter"]["statuses"]["published"] == 5
    assert report["frontmatter"]["missingRequired"] == {}
    assert report["frontmatter"]["invalidStatus"] == []
    assert report["chunks"]["total"] >= 5
    assert report["embeddings"]["dimension"] > 0


def test_knowledge_doctor_flags_missing_status_in_custom_root(tmp_path: Path) -> None:
    from scripts.knowledge_doctor import run_doctor

    configure_database(f"sqlite:///{tmp_path / 'doctor-custom.db'}")
    init_database()

    root = tmp_path / "docs"
    root.mkdir()
    source_root = Path("apps/api/knowledge/docs")
    for path in source_root.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if path.name == "quick-start.md":
            text = text.replace("status: published\n", "", 1)
        else:
            text = text if "status: published\n" in text else text.replace("updated_at: 2026-05-30\n", "updated_at: 2026-05-30\nstatus: published\n", 1)
        (root / path.name).write_text(text, encoding="utf-8")

    report = run_doctor(root)
    assert report["ok"] is False
    assert report["frontmatter"]["missingRequired"]["quick-start"] == ["status"]
