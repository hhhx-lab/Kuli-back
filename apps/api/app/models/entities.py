from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.types import UserDefinedType

from app.database import Base
from app.security import hash_password
from app.services.catalog import SERVICE_CATALOG


class VectorType(UserDefinedType):
    cache_ok = True

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def get_col_spec(self, **kw: object) -> str:
        return "TEXT"


@compiles(VectorType, "postgresql")
def _compile_vector_postgres(type_: VectorType, compiler: object, **kw: object) -> str:
    return f"vector({type_.dimension})"


@compiles(VectorType, "sqlite")
def _compile_vector_sqlite(type_: VectorType, compiler: object, **kw: object) -> str:
    return "TEXT"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32), default="user", index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    points: Mapped[int] = mapped_column(Integer, default=0)
    referral_code: Mapped[str] = mapped_column(String(40), unique=True, index=True, default=lambda: new_id().split("-")[0].upper())
    referred_by_user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    email_verified_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[str] = mapped_column(String(64))
    used_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_ip: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[str] = mapped_column(String(64))
    used_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_ip: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class ReferralReward(Base):
    __tablename__ = "referral_rewards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    referrer_user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    referred_user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), unique=True, index=True)
    points: Mapped[int] = mapped_column(Integer, default=20)
    reason: Mapped[str] = mapped_column(String(120), default="invited_registration")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    slug: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    tag: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    details_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), default="游客")
    contact: Mapped[str] = mapped_column(String(255))
    service_slug: Mapped[str] = mapped_column(String(100), default="not-sure", index=True)
    category: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(200))
    demand: Mapped[str] = mapped_column(Text)
    original_demand: Mapped[str] = mapped_column(Text, default="")
    polished_demand: Mapped[str] = mapped_column(Text, default="")
    urgency: Mapped[str] = mapped_column(String(80), default="先聊聊")
    budget: Mapped[str] = mapped_column(String(80), default="先报价看看")
    remote_help: Mapped[str] = mapped_column(String(80), default="看情况")
    intent: Mapped[str] = mapped_column(String(60), default="consultation", index=True)
    missing_fields: Mapped[str] = mapped_column(Text, default="[]")
    service_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    customer_expectation: Mapped[str] = mapped_column(Text, default="")
    quoted_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(60), default="submitted", index=True)
    ai_status: Mapped[str] = mapped_column(String(120), default="等待酷里判断需求")
    priority: Mapped[str] = mapped_column(String(60), default="normal", index=True)
    next_action: Mapped[str] = mapped_column(Text, default="确认需求范围和材料是否齐全")
    assigned_admin_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    public_notes: Mapped[str] = mapped_column(Text, default="小纸条已收到，酷里会先判断是否适合做。")
    internal_notes: Mapped[str] = mapped_column(Text, default="")
    last_customer_activity_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    last_admin_activity_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_automation_run_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    status: Mapped[str] = mapped_column(String(60))
    note: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderMessage(Base):
    __tablename__ = "order_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    author_user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(32), default="public")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderAttachment(Base):
    __tablename__ = "order_attachments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    uploader_user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str] = mapped_column(String(120))
    bucket: Mapped[str] = mapped_column(String(160), default="local")
    storage_key: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(160), default="")
    visibility: Mapped[str] = mapped_column(String(32), default="public")
    scan_status: Mapped[str] = mapped_column(String(60), default="metadata_only")
    parsed_summary: Mapped[str] = mapped_column(Text, default="")
    scan_error: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_scanned_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(60))
    note: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="sent")
    created_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(60))
    method: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(60))
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    storage_key: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    scope: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    source: Mapped[str] = mapped_column(String(200), default="service_catalog")
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    article_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_articles.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    slug: Mapped[str] = mapped_column(String(120), default="", index=True)
    source_path: Mapped[str] = mapped_column(Text, default="")
    section: Mapped[str] = mapped_column(String(200), default="")
    anchor: Mapped[str] = mapped_column(String(160), default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    chunk_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_chunks.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80), default="local-rules")
    model: Mapped[str] = mapped_column(String(120), default="local-rules")
    vector_dimension: Mapped[int] = mapped_column(Integer, default=1536)
    embedding_json: Mapped[str] = mapped_column(Text, default="[]")
    embedding_vector: Mapped[str | None] = mapped_column(VectorType(1536), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    visitor_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    page_path: Mapped[str] = mapped_column(String(255), default="/")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("agent_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    actions_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    session_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("agent_sessions.id"), nullable=True, index=True)
    order_number: Mapped[str | None] = mapped_column(String(64), ForeignKey("orders.order_number"), nullable=True, index=True)
    tool_name: Mapped[str] = mapped_column(String(160))
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(60), default="succeeded")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderAutomationSuggestion(Base):
    __tablename__ = "order_automation_suggestions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    kind: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(Text)
    suggested_status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    suggested_message: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.6)
    status: Mapped[str] = mapped_column(String(60), default="open", index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    source_refs: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    resolved_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OrderTodo(Base):
    __tablename__ = "order_todos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    source: Mapped[str] = mapped_column(String(80), default="automation")
    status: Mapped[str] = mapped_column(String(60), default="open", index=True)
    due_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderAISummary(Base):
    __tablename__ = "order_ai_summaries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    risk_flags: Mapped[str] = mapped_column(Text, default="[]")
    suggested_questions: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class OrderReplyDraft(Base):
    __tablename__ = "order_reply_drafts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_number"), index=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="draft")
    created_by: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    order_number: Mapped[str | None] = mapped_column(String(64), ForeignKey("orders.order_number"), nullable=True)
    actor_user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(160))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), default="", index=True)
    ip_address: Mapped[str] = mapped_column(String(80), default="", index=True)
    visitor_id: Mapped[str] = mapped_column(String(120), default="", index=True)
    action: Mapped[str] = mapped_column(String(160), index=True)
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String(80), default="system", index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id"), nullable=True, index=True)
    notification_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("notifications.id"), nullable=True, index=True)
    order_number: Mapped[str | None] = mapped_column(String(64), ForeignKey("orders.order_number"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(80))
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    idempotency_key: Mapped[str] = mapped_column(String(220), default="", index=True)
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=now_iso)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(80), index=True)
    order_number: Mapped[str | None] = mapped_column(String(64), ForeignKey("orders.order_number"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(60), default="unread", index=True)
    target_url: Mapped[str] = mapped_column(String(255), default="")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=now_iso)
    read_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


def seed_database(db: Session) -> None:
    from app.services.knowledge import PUBLIC_KNOWLEDGE_ARTICLES, upsert_knowledge_article

    if not db.get(User, "user_admin"):
        db.add_all(
            [
                User(
                    id="user_admin",
                    email="admin@kuli.local",
                    password_hash=hash_password("KuliAdmin123!"),
                    role="admin",
                    display_name="酷里管理员",
                    referral_code="ADMINDEMO",
                ),
                User(
                    id="user_demo",
                    email="demo@kuli.local",
                    password_hash=hash_password("KuliUser123!"),
                    role="user",
                    display_name="Demo 用户",
                    referral_code="DEMOKULI",
                ),
                User(
                    id="user_other",
                    email="other@kuli.local",
                    password_hash=hash_password("KuliOther123!"),
                    role="user",
                    display_name="Other 用户",
                    referral_code="OTHERKULI",
                ),
            ]
        )
    for item in SERVICE_CATALOG:
        if not db.get(ServiceCategory, item["slug"]):
            db.add(ServiceCategory(slug=item["slug"], title=item["title"], tag=item["tag"], summary=item["summary"], details_json=item["json"]))
        else:
            service = db.get(ServiceCategory, item["slug"])
            service.title = item["title"]
            service.tag = item["tag"]
            service.summary = item["summary"]
            service.details_json = item["json"]
            service.updated_at = now_iso()
        upsert_knowledge_article(
            db,
            scope="service",
            title=item["title"],
            body=item["knowledge_body"],
            tags=item["tags"],
            source=f"service:{item['slug']}",
        )
    for item in PUBLIC_KNOWLEDGE_ARTICLES:
        upsert_knowledge_article(db, scope=item["scope"], title=item["title"], body=item["body"], tags=item["tags"], source=item["source"])
    if not db.query(Order).first():
        db.add_all(
            [
                Order(
                    order_number="KULI-DEMO-001",
                    owner_user_id="user_demo",
                    customer_name="Demo 用户",
                    contact="demo@kuli.local",
                    service_slug="tool-development",
                    category="小工具开发",
                    title="课程项目网页 demo",
                    demand="想做一个课程项目网页 demo，有设计稿，希望先出一个能演示的版本。",
                    original_demand="想做一个课程项目网页 demo，有设计稿，希望先出一个能演示的版本。",
                    polished_demand="用户希望制作课程项目网页 demo，并先交付一个可演示版本。",
                    intent="quote_request",
                    quoted_price=180,
                    cost=60,
                    profit=120,
                    status="clarifying",
                    ai_status="需要确认范围和页面数量",
                    next_action="追问页面数量、演示截止时间和是否需要部署",
                    public_notes="酷里正在确认需求范围。",
                    internal_notes="Demo 种子订单，用于验证一般账号权限。",
                ),
                Order(
                    order_number="KULI-OTHER-001",
                    owner_user_id="user_other",
                    customer_name="Other 用户",
                    contact="other@kuli.local",
                    service_slug="document-processing",
                    category="文档处理",
                    title="PDF 翻译并保留格式",
                    demand="PDF 需要翻译，还要尽量保留排版。",
                    original_demand="PDF 需要翻译，还要尽量保留排版。",
                    polished_demand="用户需要 PDF 翻译并尽量保留原排版。",
                    intent="ready_to_start",
                    quoted_price=120,
                    cost=40,
                    profit=80,
                    status="submitted",
                    ai_status="等待检查 PDF 质量和页数",
                    next_action="请用户上传 PDF 并说明截止时间",
                    public_notes="已收到材料。",
                    internal_notes="用于验证越权访问被拒绝。",
                ),
            ]
        )
    db.commit()
