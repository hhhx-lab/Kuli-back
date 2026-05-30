"""create kuli v2 schema

Revision ID: 0001_kuli_v2_schema
Revises:
Create Date: 2026-05-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_kuli_v2_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_articles_scope"), "knowledge_articles", ["scope"], unique=False)

    op.create_table(
        "service_categories",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("tag", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("referral_code", sa.String(length=40), nullable=False),
        sa.Column("referred_by_user_id", sa.String(length=64), nullable=True),
        sa.Column("email_verified_at", sa.String(length=64), nullable=True),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["referred_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_referral_code"), "users", ["referral_code"], unique=True)
    op.create_index(op.f("ix_users_referred_by_user_id"), "users", ["referred_by_user_id"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.String(length=64), nullable=False),
        sa.Column("used_at", sa.String(length=64), nullable=True),
        sa.Column("created_ip", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_verification_tokens_token_hash"), "email_verification_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_email_verification_tokens_user_id"), "email_verification_tokens", ["user_id"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.String(length=64), nullable=False),
        sa.Column("used_at", sa.String(length=64), nullable=True),
        sa.Column("created_ip", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_reset_tokens_token_hash"), "password_reset_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"], unique=False)

    op.create_table(
        "referral_rewards",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("referrer_user_id", sa.String(length=64), nullable=False),
        sa.Column("referred_user_id", sa.String(length=64), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["referred_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["referrer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_referral_rewards_referred_user_id"), "referral_rewards", ["referred_user_id"], unique=True)
    op.create_index(op.f("ix_referral_rewards_referrer_user_id"), "referral_rewards", ["referrer_user_id"], unique=False)

    op.create_table(
        "agent_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("visitor_id", sa.String(length=120), nullable=True),
        sa.Column("page_path", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("article_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("section", sa.String(length=200), nullable=False),
        sa.Column("anchor", sa.String(length=160), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["knowledge_articles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_article_id"), "knowledge_chunks", ["article_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_slug"), "knowledge_chunks", ["slug"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("owner_user_id", sa.String(length=64), nullable=True),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("contact", sa.String(length=255), nullable=False),
        sa.Column("service_slug", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("demand", sa.Text(), nullable=False),
        sa.Column("original_demand", sa.Text(), nullable=False),
        sa.Column("polished_demand", sa.Text(), nullable=False),
        sa.Column("urgency", sa.String(length=80), nullable=False),
        sa.Column("budget", sa.String(length=80), nullable=False),
        sa.Column("remote_help", sa.String(length=80), nullable=False),
        sa.Column("intent", sa.String(length=60), nullable=False),
        sa.Column("missing_fields", sa.Text(), nullable=False),
        sa.Column("service_confidence", sa.Float(), nullable=False),
        sa.Column("customer_expectation", sa.Text(), nullable=False),
        sa.Column("quoted_price", sa.Float(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("profit", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("ai_status", sa.String(length=120), nullable=False),
        sa.Column("priority", sa.String(length=60), nullable=False),
        sa.Column("next_action", sa.Text(), nullable=False),
        sa.Column("assigned_admin_id", sa.String(length=64), nullable=True),
        sa.Column("public_notes", sa.Text(), nullable=False),
        sa.Column("internal_notes", sa.Text(), nullable=False),
        sa.Column("last_customer_activity_at", sa.String(length=64), nullable=False),
        sa.Column("last_admin_activity_at", sa.String(length=64), nullable=True),
        sa.Column("last_automation_run_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_intent"), "orders", ["intent"], unique=False)
    op.create_index(op.f("ix_orders_order_number"), "orders", ["order_number"], unique=True)
    op.create_index(op.f("ix_orders_owner_user_id"), "orders", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_orders_priority"), "orders", ["priority"], unique=False)
    op.create_index(op.f("ix_orders_service_slug"), "orders", ["service_slug"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=True),
        sa.Column("actor_user_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=80), nullable=False),
        sa.Column("visitor_id", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_audit_logs_action"), "security_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_email"), "security_audit_logs", ["email"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_ip_address"), "security_audit_logs", ["ip_address"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_user_id"), "security_audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_visitor_id"), "security_audit_logs", ["visitor_id"], unique=False)

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("actions_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_session_id"), "agent_messages", ["session_id"], unique=False)

    op.create_table(
        "agent_tool_calls",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("order_number", sa.String(length=64), nullable=True),
        sa.Column("tool_name", sa.String(length=160), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_tool_calls_order_number"), "agent_tool_calls", ["order_number"], unique=False)
    op.create_index(op.f("ix_agent_tool_calls_session_id"), "agent_tool_calls", ["session_id"], unique=False)

    op.create_table(
        "deliverables",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deliverables_order_number"), "deliverables", ["order_number"], unique=False)

    op.create_table(
        "knowledge_embeddings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("vector_dimension", sa.Integer(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("embedding_vector", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["knowledge_chunks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE knowledge_embeddings ALTER COLUMN embedding_vector TYPE vector(1536) USING embedding_vector::vector(1536)")
        op.execute(
            "CREATE INDEX ix_knowledge_embeddings_embedding_vector "
            "ON knowledge_embeddings USING hnsw (embedding_vector vector_cosine_ops)"
        )
    op.create_index(op.f("ix_knowledge_embeddings_chunk_id"), "knowledge_embeddings", ["chunk_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("target_url", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("read_at", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_order_number"), "notifications", ["order_number"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)
    op.create_index(op.f("ix_notifications_type"), "notifications", ["type"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)

    op.create_table(
        "notification_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("notification_id", sa.String(length=64), nullable=True),
        sa.Column("order_number", sa.String(length=64), nullable=True),
        sa.Column("channel", sa.String(length=80), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=220), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notification_events_event_type"), "notification_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_notification_events_idempotency_key"), "notification_events", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_notification_events_notification_id"), "notification_events", ["notification_id"], unique=False)
    op.create_index(op.f("ix_notification_events_order_number"), "notification_events", ["order_number"], unique=False)
    op.create_index(op.f("ix_notification_events_user_id"), "notification_events", ["user_id"], unique=False)

    op.create_table(
        "order_ai_summaries",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("risk_flags", sa.Text(), nullable=False),
        sa.Column("suggested_questions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_ai_summaries_order_number"), "order_ai_summaries", ["order_number"], unique=False)

    op.create_table(
        "order_attachments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("uploader_user_id", sa.String(length=64), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("bucket", sa.String(length=160), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=160), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("scan_status", sa.String(length=60), nullable=False),
        sa.Column("parsed_summary", sa.Text(), nullable=False),
        sa.Column("scan_error", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("last_scanned_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.ForeignKeyConstraint(["uploader_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_attachments_order_number"), "order_attachments", ["order_number"], unique=False)

    op.create_table(
        "order_automation_suggestions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=60), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("suggested_status", sa.String(length=60), nullable=True),
        sa.Column("suggested_message", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("source_refs", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.Column("resolved_at", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_automation_suggestions_order_number"), "order_automation_suggestions", ["order_number"], unique=False)
    op.create_index(op.f("ix_order_automation_suggestions_status"), "order_automation_suggestions", ["status"], unique=False)

    op.create_table(
        "order_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_events_order_number"), "order_events", ["order_number"], unique=False)

    op.create_table(
        "order_messages",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("author_user_id", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_messages_order_number"), "order_messages", ["order_number"], unique=False)

    op.create_table(
        "order_reply_drafts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_reply_drafts_order_number"), "order_reply_drafts", ["order_number"], unique=False)

    op.create_table(
        "order_todos",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("due_at", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_todos_order_number"), "order_todos", ["order_number"], unique=False)
    op.create_index(op.f("ix_order_todos_status"), "order_todos", ["status"], unique=False)

    op.create_table(
        "payment_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(length=60), nullable=False),
        sa.Column("method", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_records_order_number"), "payment_records", ["order_number"], unique=False)

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("kind", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_number"], ["orders.order_number"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotes_order_number"), "quotes", ["order_number"], unique=False)


def downgrade() -> None:
    for table_name in [
        "quotes",
        "payment_records",
        "order_todos",
        "order_reply_drafts",
        "order_messages",
        "order_events",
        "order_automation_suggestions",
        "order_attachments",
        "order_ai_summaries",
        "notification_events",
        "notifications",
        "knowledge_embeddings",
        "deliverables",
        "agent_tool_calls",
        "agent_messages",
        "security_audit_logs",
        "admin_audit_logs",
        "orders",
        "knowledge_chunks",
        "agent_sessions",
        "password_reset_tokens",
        "email_verification_tokens",
        "referral_rewards",
        "users",
        "service_categories",
        "knowledge_articles",
    ]:
        op.drop_table(table_name)
