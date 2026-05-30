import json

from sqlalchemy.orm import Session

from app.models.entities import KnowledgeArticle, KnowledgeChunk, KnowledgeEmbedding, now_iso
from app.services.embeddings import embed_text, vector_to_json, vector_to_pg_literal


PUBLIC_KNOWLEDGE_ARTICLES = [
    {
        "scope": "rule",
        "title": "咨询与收费边界",
        "body": "酷里可以先免费判断能不能做。小需求在范围清楚、风险可控时可以验收后付款；复杂需求、开发、部署、远程排查或多轮沟通可能先收定金。小酷不能替管理员承诺固定价格、周期或第三方平台结果。",
        "tags": ["收费", "咨询", "定金", "报价", "边界"],
        "source": "rule:payment-boundary",
    },
    {
        "scope": "rule",
        "title": "材料准备规则",
        "body": "用户不用先写专业方案。更有用的材料包括截图、源文件、报错日志、目标效果、截止时间、预算区间和是否方便远程协助。说不清时可以直接发截图并说明“我现在卡在这里”。",
        "tags": ["材料", "截图", "源文件", "报错", "小纸条"],
        "source": "rule:required-materials",
    },
    {
        "scope": "rule",
        "title": "订单状态说明",
        "body": "submitted 表示小纸条已提交；clarifying 表示正在追问材料；quoted 表示已报价；deposit_pending 表示等待定金；in_progress 表示处理中；review 表示等待验收；final_payment_pending 表示等待尾款；completed 表示已完成；cancelled 表示已取消。",
        "tags": ["订单", "状态", "进度", "验收", "尾款"],
        "source": "rule:order-status",
    },
    {
        "scope": "safety",
        "title": "小酷安全边界",
        "body": "小酷只能回答公开服务知识、材料准备、收费边界和当前登录用户自己的订单摘要。小酷不能读取内部成本、利润、管理员备注、其他用户订单，也不能要求用户泄露敏感密码。",
        "tags": ["小酷", "安全", "权限", "隐私", "内部字段"],
        "source": "safety:xiaoku-boundary",
    },
    {
        "scope": "faq",
        "title": "不会描述需求怎么办",
        "body": "不会描述需求时，可以直接发截图、文件或报错，再写一句想达到的效果。酷里会先帮你判断属于哪类服务、还缺什么材料、是否适合进入正式订单。",
        "tags": ["FAQ", "需求", "截图", "不知道怎么分"],
        "source": "faq:unclear-demand",
    },
]


def serialize_knowledge_article(row: KnowledgeArticle) -> dict[str, object]:
    return {
        "id": row.id,
        "scope": row.scope,
        "title": row.title,
        "body": row.body,
        "tags": json.loads(row.tags or "[]"),
        "source": row.source,
        "updatedAt": row.updated_at,
    }


def upsert_knowledge_article(db: Session, *, scope: str, title: str, body: str, tags: str | list[str], source: str) -> KnowledgeArticle:
    tags_json = tags if isinstance(tags, str) else json.dumps(tags, ensure_ascii=False)
    slug = source.split(":", 1)[1] if ":" in source else source
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.source == source).first()
    if article:
        article.scope = scope
        article.title = title
        article.body = body
        article.tags = tags_json
        article.updated_at = now_iso()
    else:
        article = KnowledgeArticle(scope=scope, title=title, body=body, tags=tags_json, source=source)
        db.add(article)
        db.flush()

    chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.article_id == article.id, KnowledgeChunk.chunk_index == 0).first()
    if chunk:
        chunk.content = body
        chunk.token_count = len(body)
        chunk.slug = slug
        chunk.source_path = source
        chunk.section = title
        chunk.anchor = slug
        chunk.priority = 0
        chunk.updated_at = now_iso()
    else:
        chunk = KnowledgeChunk(
            article_id=article.id,
            chunk_index=0,
            slug=slug,
            source_path=source,
            section=title,
            anchor=slug,
            priority=0,
            content=body,
            token_count=len(body),
        )
        db.add(chunk)
        db.flush()

    ensure_chunk_embedding(db, chunk, allow_remote=False)
    return article


def ensure_chunk_embedding(db: Session, chunk: KnowledgeChunk, *, allow_remote: bool = True, force: bool = False) -> bool:
    embedding = db.query(KnowledgeEmbedding).filter(KnowledgeEmbedding.chunk_id == chunk.id).first()
    if embedding and not force and embedding.embedding_json and embedding.embedding_json != "[]":
        return False

    result = embed_text(chunk.content, allow_remote=allow_remote)
    if embedding:
        embedding.provider = result.provider
        embedding.model = result.model
        embedding.vector_dimension = len(result.vector)
        embedding.embedding_json = vector_to_json(result.vector)
        embedding.embedding_vector = vector_to_pg_literal(result.vector)
        return True

    db.add(
        KnowledgeEmbedding(
            chunk_id=chunk.id,
            provider=result.provider,
            model=result.model,
            vector_dimension=len(result.vector),
            embedding_json=vector_to_json(result.vector),
            embedding_vector=vector_to_pg_literal(result.vector),
        )
    )
    return True
