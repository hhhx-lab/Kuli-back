import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from urllib.parse import quote, unquote

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database import get_db, init_database
from app.models.entities import (
    AgentSession,
    AdminAuditLog,
    Deliverable,
    Order,
    OrderAISummary,
    OrderAttachment,
    OrderAutomationSuggestion,
    OrderEvent,
    OrderMessage,
    OrderTodo,
    PaymentRecord,
    Quote,
    ReferralReward,
    User,
    now_iso,
)
from app.notifications.events import create_email_verification_event, create_order_message_notification, create_password_reset_event
from app.notifications.in_app import list_notifications, mark_all_read, mark_read, serialize_notification, unread_count
from app.schemas.api import (
    AdminOrderPatch,
    AdminOrderEnvelope,
    AdminOrdersOut,
    AgentChatInput,
    AgentChatOut,
    AgentSessionInput,
    AgentSessionEnvelope,
    AssistantSummaryOut,
    AttachmentDownloadEnvelope,
    AttachmentInput,
    AuthIn,
    AuthOut,
    DeliverableInput,
    DocEnvelope,
    DocSearchOut,
    DocsOut,
    HealthDepsOut,
    HealthOut,
    KnowledgeArticlesOut,
    MessageInput,
    NoteInput,
    NotificationEnvelope,
    NotificationsOut,
    NotificationsReadAllOut,
    NotificationUnreadCountOut,
    OrderEnvelope,
    OrdersOut,
    PolishOut,
    PaymentInput,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    PresignedUploadEnvelope,
    PolishInput,
    QuoteInput,
    RegisterIn,
    ServiceEnvelope,
    ServiceOut,
    ServicesOut,
    StatusOut,
    TokenConfirmIn,
    UserEnvelope,
    UserProfileEnvelope,
    UserProfilePatch,
    UserReferralEnvelope,
    UserSummaryEnvelope,
    UploadPresignInput,
)
from app.security import hash_password, sign_token, verify_password, verify_token
from app.services.auth_tokens import (
    find_active_email_verification_token,
    find_active_password_reset_token,
    issue_email_verification_token,
    issue_password_reset_token,
    mark_token_used,
)
from app.services.automation import ensure_automation_for_order, polish_demand
from app.services.catalog import SERVICE_CATALOG, catalog_item
from app.services.docs import doc_detail, doc_summary, get_doc, load_docs, search_docs
from app.services.health import dependency_report
from app.services.knowledge import serialize_knowledge_article
from app.services.rag import search_knowledge
from app.services.security_controls import (
    check_agent_rate_limit,
    check_register_rate_limit,
    client_ip,
    is_locked,
    record_failed_login,
    record_security_event,
    record_successful_login,
    validate_password,
)
from app.services.storage import create_presigned_download, create_presigned_upload, local_object_path, verify_local_download_signature
from app.services.xiaoku import chat as xiaoku_chat
from app.services.xiaoku import create_session as create_xiaoku_session
from app.tasks.attachment_tasks import analyze_attachment, analyze_attachment_sync


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield


app = FastAPI(title="Kuli 2.0 API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def public_user(user: User) -> dict[str, str]:
    return {"id": user.id, "email": user.email, "role": user.role, "displayName": user.display_name}


def public_profile(user: User) -> dict[str, object]:
    return {
        **public_user(user),
        "points": user.points,
        "referralCode": user.referral_code,
        "referredByUserId": user.referred_by_user_id,
        "emailVerifiedAt": user.email_verified_at,
        "createdAt": user.created_at,
    }


def auth_response(user: User) -> AuthOut:
    token = sign_token({"sub": user.id, "email": user.email, "role": user.role})
    return AuthOut(token=token, user=public_user(user))


def current_user_optional(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = verify_token(authorization.removeprefix("Bearer ").strip())
    if not payload:
        return None
    return db.get(User, payload.get("sub"))


def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def current_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="没有管理员权限")
    return user


def canonical_storage_key(object_key: str) -> str:
    return quote(unquote(object_key), safe="/")


def next_order_number(db: Session) -> str:
    count = db.query(Order).count() + 1
    return f"KULI-{count:06d}"


def next_referral_code(db: Session, email: str) -> str:
    prefix = "".join(char for char in email.split("@", 1)[0].upper() if char.isalnum())[:5] or "KULI"
    for index in range(1, 1000):
        code = f"{prefix}{index:03d}"
        if not db.query(User).filter(User.referral_code == code).first():
            return code
    raise HTTPException(status_code=500, detail="邀请码生成失败")


def frontend_base_url(request: Request) -> str:
    origin = request.headers.get("origin")
    if origin:
        return origin
    return settings.cors_origin_list[0] if settings.cors_origin_list else "http://127.0.0.1:3000"


def order_events(db: Session, order_number: str) -> list[dict[str, object]]:
    return [
        {"id": row.id, "status": row.status, "note": row.note, "createdBy": row.created_by, "createdAt": row.created_at}
        for row in db.query(OrderEvent).filter(OrderEvent.order_number == order_number).order_by(OrderEvent.created_at.asc()).all()
    ]


def order_messages(db: Session, order_number: str, include_internal: bool) -> list[dict[str, object]]:
    query = db.query(OrderMessage).filter(OrderMessage.order_number == order_number)
    if not include_internal:
        query = query.filter(OrderMessage.visibility == "public")
    return [
        {"id": row.id, "authorUserId": row.author_user_id, "body": row.body, "visibility": row.visibility, "createdAt": row.created_at}
        for row in query.order_by(OrderMessage.created_at.asc()).all()
    ]


def order_attachments(db: Session, order_number: str, include_internal: bool) -> list[dict[str, object]]:
    query = db.query(OrderAttachment).filter(OrderAttachment.order_number == order_number)
    if not include_internal:
        query = query.filter(OrderAttachment.visibility == "public")
    return [
        {
            "id": row.id,
            "fileName": row.file_name,
            "fileSize": row.file_size,
            "contentType": row.content_type,
            "bucket": row.bucket,
            "storageKey": row.storage_key,
            "visibility": row.visibility,
            "scanStatus": row.scan_status,
            "parsedSummary": row.parsed_summary,
            "scanError": row.scan_error,
            "retryCount": row.retry_count,
            "lastScannedAt": row.last_scanned_at,
            "createdAt": row.created_at,
        }
        for row in query.order_by(OrderAttachment.created_at.asc()).all()
    ]


def automation_suggestions(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = (
        db.query(OrderAutomationSuggestion)
        .filter(OrderAutomationSuggestion.order_number == order_number)
        .order_by(OrderAutomationSuggestion.created_at.desc())
        .limit(12)
        .all()
    )
    return [
        {
            "id": row.id,
            "kind": row.kind,
            "severity": row.severity,
            "summary": row.summary,
            "suggestedStatus": row.suggested_status,
            "suggestedMessage": row.suggested_message,
            "confidence": row.confidence,
            "status": row.status,
            "reason": row.reason,
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_quotes(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = db.query(Quote).filter(Quote.order_number == order_number).order_by(Quote.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "amount": row.amount,
            "kind": row.kind,
            "note": row.note,
            "status": row.status,
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_payments(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = db.query(PaymentRecord).filter(PaymentRecord.order_number == order_number).order_by(PaymentRecord.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "amount": row.amount,
            "kind": row.kind,
            "method": row.method,
            "status": row.status,
            "note": row.note,
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_deliverables(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = db.query(Deliverable).filter(Deliverable.order_number == order_number).order_by(Deliverable.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "storageKey": row.storage_key,
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_todos(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = db.query(OrderTodo).filter(OrderTodo.order_number == order_number).order_by(OrderTodo.created_at.desc()).limit(20).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "source": row.source,
            "status": row.status,
            "dueAt": row.due_at,
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_ai_summaries(db: Session, order_number: str) -> list[dict[str, object]]:
    rows = db.query(OrderAISummary).filter(OrderAISummary.order_number == order_number).order_by(OrderAISummary.created_at.desc()).limit(8).all()
    return [
        {
            "id": row.id,
            "summary": row.summary,
            "riskFlags": json.loads(row.risk_flags or "[]"),
            "suggestedQuestions": json.loads(row.suggested_questions or "[]"),
            "createdAt": row.created_at,
        }
        for row in rows
    ]


def order_payload(db: Session, order: Order, admin: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": order.id,
        "orderNumber": order.order_number,
        "customerName": order.customer_name,
        "contact": order.contact,
        "serviceSlug": order.service_slug,
        "category": order.category,
        "title": order.title,
        "demand": order.demand,
        "originalDemand": order.original_demand or order.demand,
        "polishedDemand": order.polished_demand or order.demand,
        "urgency": order.urgency,
        "budget": order.budget,
        "remoteHelp": order.remote_help,
        "intent": order.intent,
        "missingFields": json.loads(order.missing_fields or "[]"),
        "serviceConfidence": order.service_confidence,
        "quotedPrice": order.quoted_price,
        "status": order.status,
        "aiStatus": order.ai_status,
        "nextAction": order.next_action,
        "publicNotes": order.public_notes,
        "createdAt": order.created_at,
        "updatedAt": order.updated_at,
        "events": order_events(db, order.order_number),
        "messages": order_messages(db, order.order_number, admin),
        "attachments": order_attachments(db, order.order_number, admin),
        "quotes": order_quotes(db, order.order_number),
        "payments": order_payments(db, order.order_number),
        "deliverables": order_deliverables(db, order.order_number),
    }
    if admin:
        suggestions = db.query(AdminAuditLog).filter(AdminAuditLog.order_number == order.order_number).count()
        payload.update(
            {
                "ownerUserId": order.owner_user_id,
                "cost": order.cost,
                "profit": order.profit,
                "priority": order.priority,
                "internalNotes": order.internal_notes,
                "assignedAdminId": order.assigned_admin_id,
                "automationAuditCount": suggestions,
                "automationSuggestions": automation_suggestions(db, order.order_number),
                "todos": order_todos(db, order.order_number),
                "aiSummaries": order_ai_summaries(db, order.order_number),
            }
        )
    return payload


def create_order_from_input(db: Session, data: NoteInput, owner: User | None) -> Order:
    service = catalog_item(data.serviceSlug or "not-sure")
    polished = polish_demand(data.originalDemand or data.demand, service["title"] if service else None, data.serviceSlug)
    intent = data.intent or str(polished["intent"])
    missing = list(polished["missingFields"])
    order = Order(
        order_number=next_order_number(db),
        owner_user_id=owner.id if owner else None,
        customer_name=owner.display_name if owner else data.customerName or "游客",
        contact=data.contact,
        service_slug=data.serviceSlug or "not-sure",
        category=data.category,
        title=(data.demand[:42] + "…") if len(data.demand) > 42 else data.demand,
        demand=str(polished["polishedDemand"]),
        original_demand=data.originalDemand or data.demand,
        polished_demand=str(polished["polishedDemand"]),
        urgency=data.urgency,
        budget=data.budget,
        remote_help=data.remoteHelp,
        intent=intent,
        missing_fields=json.dumps(missing, ensure_ascii=False),
        service_confidence=float(polished["serviceConfidence"]),
        customer_expectation=data.demand,
        status="submitted",
        ai_status="小酷已整理需求，等待酷里判断",
        next_action="追问：" + "、".join(missing) if missing else "确认范围后给出下一步报价或建议",
        internal_notes="登录账号提交订单。" if owner else "游客提交小纸条。",
    )
    db.add(order)
    db.flush()
    db.add(OrderEvent(order_number=order.order_number, status="submitted", note="订单已提交", created_by=owner.id if owner else None))
    db.commit()
    db.refresh(order)
    ensure_automation_for_order(db, order, reason="created")
    return order


@app.get("/api/health", response_model=HealthOut)
@app.get("/health", response_model=HealthOut)
def health() -> dict[str, object]:
    return {"ok": True, "service": "kuli-api", "version": "0.2.0"}


@app.get("/api/health/deps", response_model=HealthDepsOut)
def health_deps(db: Session = Depends(get_db)) -> dict[str, object]:
    return dependency_report(db, settings)


@app.get("/api/services", response_model=ServicesOut)
def list_services() -> dict[str, list[ServiceOut]]:
    return {"services": [catalog_item(item["slug"]) for item in SERVICE_CATALOG if catalog_item(item["slug"])]}


@app.get("/api/services/{slug}", response_model=ServiceEnvelope)
def get_service(slug: str) -> dict[str, object]:
    service = catalog_item(slug)
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    return {"service": service}


@app.get("/api/knowledge", response_model=KnowledgeArticlesOut)
def list_knowledge(db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    from app.models.entities import KnowledgeArticle

    rows = db.query(KnowledgeArticle).order_by(KnowledgeArticle.updated_at.desc()).all()
    return {"articles": [serialize_knowledge_article(row) for row in rows]}


@app.get("/api/knowledge/search", response_model=KnowledgeArticlesOut)
def search_knowledge_api(q: str = Query(min_length=1, max_length=200), db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    rows = search_knowledge(db, q)
    return {
        "articles": [
            serialize_knowledge_article(row)
            for row in rows
        ]
    }


@app.get("/api/docs", response_model=DocsOut)
def list_docs() -> dict[str, list[dict[str, object]]]:
    return {"docs": [doc_summary(doc) for doc in load_docs()]}


@app.get("/api/docs/search", response_model=DocSearchOut)
def search_docs_api(q: str = Query(min_length=1, max_length=200)) -> dict[str, list[dict[str, object]]]:
    return {"results": search_docs(q)}


@app.get("/api/docs/{slug}", response_model=DocEnvelope)
def get_doc_api(slug: str) -> dict[str, object]:
    doc = get_doc(slug)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"doc": doc_detail(doc)}


@app.post("/api/ai/polish-demand", response_model=PolishOut)
def polish(input_data: PolishInput) -> dict[str, object]:
    service = catalog_item(input_data.serviceSlug or "")
    return polish_demand(input_data.demand, service["title"] if service else None, input_data.serviceSlug)


@app.post("/api/auth/login", response_model=AuthOut)
def login(input_data: AuthIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    ip_address = client_ip(request)
    user = db.query(User).filter(User.email.ilike(input_data.email)).first()
    if user and is_locked(user):
        record_security_event(db, action="auth.login.locked_attempt", user_id=user.id, email=input_data.email.lower(), ip_address=ip_address)
        db.commit()
        raise HTTPException(status_code=423, detail="登录尝试过多，请稍后再试")
    if not user or not verify_password(input_data.password, user.password_hash):
        record_failed_login(db, user, email=input_data.email.lower(), ip_address=ip_address)
        raise HTTPException(status_code=401, detail="邮箱或密码不正确")
    record_successful_login(db, user)
    return auth_response(user)


@app.post("/api/auth/register", status_code=201, response_model=AuthOut)
def register(input_data: RegisterIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    ip_address = client_ip(request)
    if not check_register_rate_limit(db, ip_address):
        raise HTTPException(status_code=429, detail="注册请求过于频繁，请稍后再试")
    password_error = validate_password(input_data.email, input_data.password)
    if password_error:
        record_security_event(db, action="auth.register.weak_password", email=input_data.email.lower(), ip_address=ip_address, details={"reason": password_error})
        db.commit()
        raise HTTPException(status_code=422, detail=password_error)
    if db.query(User).filter(User.email.ilike(input_data.email)).first():
        raise HTTPException(status_code=409, detail="邮箱已注册")
    referrer = None
    if input_data.referralCode:
        referrer = db.query(User).filter(User.referral_code == input_data.referralCode.strip().upper()).first()
    user = User(
        email=input_data.email.lower(),
        password_hash=hash_password(input_data.password),
        display_name=input_data.displayName,
        role="user",
        referral_code=next_referral_code(db, input_data.email),
        referred_by_user_id=referrer.id if referrer else None,
    )
    db.add(user)
    db.flush()
    if referrer and referrer.id != user.id:
        referrer.points += 20
        db.add(ReferralReward(referrer_user_id=referrer.id, referred_user_id=user.id, points=20))
    db.commit()
    db.refresh(user)
    return auth_response(user)


@app.get("/api/auth/me", response_model=UserEnvelope)
def me(user: User = Depends(current_user)) -> dict[str, object]:
    return {"user": public_user(user)}


@app.post("/api/auth/email-verification/request", status_code=202, response_model=StatusOut)
def request_email_verification(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not user.email_verified_at:
        ip_address = client_ip(request)
        token, _ = issue_email_verification_token(db, user=user, ip_address=ip_address)
        create_email_verification_event(db, user=user, token=token, base_url=frontend_base_url(request))
        record_security_event(
            db,
            action="auth.email_verification.requested",
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
        )
        db.commit()
    return {"ok": True, "message": "如果需要验证邮件，酷里已经发出。"}


@app.post("/api/auth/email-verification/confirm", response_model=StatusOut)
def confirm_email_verification(input_data: TokenConfirmIn, db: Session = Depends(get_db)) -> dict[str, object]:
    token_row = find_active_email_verification_token(db, input_data.token)
    if not token_row:
        raise HTTPException(status_code=400, detail="验证 token 无效或已过期")
    user = db.get(User, token_row.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="验证 token 无效或已过期")
    user.email_verified_at = user.email_verified_at or now_iso()
    mark_token_used(token_row)
    record_security_event(db, action="auth.email_verification.confirmed", user_id=user.id, email=user.email)
    db.commit()
    return {"ok": True, "message": "邮箱已验证"}


@app.post("/api/auth/password-reset/request", status_code=202, response_model=StatusOut)
def request_password_reset(input_data: PasswordResetRequestIn, request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    ip_address = client_ip(request)
    user = db.query(User).filter(User.email.ilike(input_data.email)).first()
    if user:
        token, _ = issue_password_reset_token(db, user=user, ip_address=ip_address)
        create_password_reset_event(db, user=user, token=token, base_url=frontend_base_url(request))
        record_security_event(
            db,
            action="auth.password_reset.requested",
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
        )
        db.commit()
    else:
        record_security_event(
            db,
            action="auth.password_reset.requested_unknown",
            email=input_data.email.lower(),
            ip_address=ip_address,
        )
        db.commit()
    return {"ok": True, "message": "如果邮箱存在，重置邮件已经发出。"}


@app.post("/api/auth/password-reset/confirm", response_model=StatusOut)
def confirm_password_reset(input_data: PasswordResetConfirmIn, db: Session = Depends(get_db)) -> dict[str, object]:
    token_row = find_active_password_reset_token(db, input_data.token)
    if not token_row:
        raise HTTPException(status_code=400, detail="重置 token 无效或已过期")
    user = db.get(User, token_row.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="重置 token 无效或已过期")
    password_error = validate_password(user.email, input_data.password)
    if password_error:
        record_security_event(db, action="auth.password_reset.weak_password", user_id=user.id, email=user.email, details={"reason": password_error})
        db.commit()
        raise HTTPException(status_code=422, detail=password_error)
    user.password_hash = hash_password(input_data.password)
    user.failed_login_count = 0
    user.locked_until = None
    mark_token_used(token_row)
    record_security_event(db, action="auth.password_reset.confirmed", user_id=user.id, email=user.email)
    db.commit()
    return {"ok": True, "message": "密码已重置"}


@app.get("/api/me/profile", response_model=UserProfileEnvelope)
def me_profile(user: User = Depends(current_user)) -> dict[str, object]:
    return {"profile": public_profile(user)}


@app.patch("/api/me/profile", response_model=UserProfileEnvelope)
def patch_me_profile(input_data: UserProfilePatch, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    user.display_name = input_data.displayName
    db.commit()
    db.refresh(user)
    return {"profile": public_profile(user)}


@app.get("/api/me/summary", response_model=UserSummaryEnvelope)
def me_summary(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.query(Order).filter(Order.owner_user_id == user.id).order_by(Order.updated_at.desc()).all()
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = by_status.get(row.status, 0) + 1
    recent = [
        {
            "orderNumber": row.order_number,
            "title": row.title,
            "status": row.status,
            "nextAction": row.next_action,
            "updatedAt": row.updated_at,
        }
        for row in rows[:5]
    ]
    return {
        "summary": {
            "profile": public_profile(user),
            "orders": {"total": len(rows), "byStatus": by_status},
            "recentOrders": recent,
            "points": {"current": user.points, "nextLevel": 100, "progress": min(user.points, 100)},
        }
    }


@app.get("/api/me/referral", response_model=UserReferralEnvelope)
def me_referral(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    rewards = db.query(ReferralReward).filter(ReferralReward.referrer_user_id == user.id).order_by(ReferralReward.created_at.desc()).all()
    return {
        "referral": {
            "referralCode": user.referral_code,
            "invitePath": f"/login?referralCode={user.referral_code}",
            "points": user.points,
            "rewardedInvites": len(rewards),
            "rewards": [
                {"id": row.id, "points": row.points, "reason": row.reason, "createdAt": row.created_at}
                for row in rewards[:20]
            ],
        }
    }


@app.get("/api/notifications", response_model=NotificationsOut)
def my_notifications(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rows = list_notifications(db, user.id, status=status, limit=limit)
    return {"notifications": [serialize_notification(row) for row in rows]}


@app.get("/api/notifications/unread-count", response_model=NotificationUnreadCountOut)
def my_notifications_unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    return {"unreadCount": unread_count(db, user.id)}


@app.patch("/api/notifications/read-all", response_model=NotificationsReadAllOut)
def read_all_notifications(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    return {"updated": mark_all_read(db, user.id)}


@app.patch("/api/notifications/{notification_id}/read", response_model=NotificationEnvelope)
def read_notification(notification_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    notification = mark_read(db, user.id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"notification": serialize_notification(notification)}


@app.post("/api/inquiries", status_code=201, response_model=OrderEnvelope)
@app.post("/api/public/inquiries", status_code=201, response_model=OrderEnvelope)
def create_public_inquiry(input_data: NoteInput, db: Session = Depends(get_db)) -> dict[str, object]:
    order = create_order_from_input(db, input_data, owner=None)
    return {"order": order_payload(db, order)}


@app.get("/api/orders", response_model=OrdersOut)
def my_orders(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    rows = db.query(Order).filter(Order.owner_user_id == user.id).order_by(Order.updated_at.desc()).all()
    return {"orders": [order_payload(db, row) for row in rows]}


@app.post("/api/orders", status_code=201, response_model=OrderEnvelope)
def create_user_order(input_data: NoteInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    order = create_order_from_input(db, input_data, owner=user)
    return {"order": order_payload(db, order)}


@app.get("/api/orders/{order_number}", response_model=OrderEnvelope)
def my_order(order_number: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number, Order.owner_user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"order": order_payload(db, order)}


@app.post("/api/orders/{order_number}/messages", status_code=201, response_model=OrderEnvelope)
def add_message(order_number: str, input_data: MessageInput, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number, Order.owner_user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    db.add(OrderMessage(order_number=order_number, author_user_id=user.id, body=input_data.body))
    order.last_customer_activity_at = now_iso()
    order.updated_at = now_iso()
    db.commit()
    ensure_automation_for_order(db, order, reason="customer_message")
    return {"order": order_payload(db, order)}


@app.post("/api/orders/{order_number}/accept", response_model=OrderEnvelope)
def accept_order(order_number: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number, Order.owner_user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "completed":
        return {"order": order_payload(db, order)}
    if order.status != "review":
        raise HTTPException(status_code=409, detail="订单尚未进入验收状态")
    received = sum(row.amount for row in db.query(PaymentRecord).filter(PaymentRecord.order_number == order_number, PaymentRecord.status == "received").all())
    if order.quoted_price and received < order.quoted_price:
        order.status = "final_payment_pending"
        order.next_action = "客户已验收，等待确认尾款"
        note = "客户已验收，等待尾款"
    else:
        order.status = "completed"
        order.next_action = "订单已完成"
        order.public_notes = "客户已验收，订单完成。"
        note = "客户已验收并完成订单"
    order.last_customer_activity_at = now_iso()
    order.updated_at = now_iso()
    db.add(OrderEvent(order_number=order_number, status=order.status, note=note, created_by=user.id))
    db.commit()
    db.refresh(order)
    ensure_automation_for_order(db, order, reason="customer_acceptance")
    return {"order": order_payload(db, order)}


@app.post("/api/uploads/presign", status_code=201, response_model=PresignedUploadEnvelope)
def presign_upload(
    input_data: UploadPresignInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if input_data.orderNumber:
        order = db.query(Order).filter(Order.order_number == input_data.orderNumber).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        if user.role != "admin" and order.owner_user_id != user.id:
            raise HTTPException(status_code=403, detail="不能给其他用户订单上传附件")
    presign = create_presigned_upload(input_data.fileName, input_data.contentType, input_data.orderNumber, input_data.fileSize)
    return {
        "upload": {
            "provider": presign.provider,
            "bucket": presign.bucket,
            "objectKey": presign.object_key,
            "uploadUrl": presign.upload_url,
            "publicUrl": presign.public_url,
            "fields": presign.fields,
        }
    }


@app.get("/api/uploads/local/{object_key:path}")
def download_local_upload(object_key: str, expires: int = Query(), signature: str = Query()) -> FileResponse:
    canonical_object_key = canonical_storage_key(object_key)
    if not verify_local_download_signature(canonical_object_key, expires, signature):
        raise HTTPException(status_code=403, detail="下载链接已失效或签名不正确")
    try:
        path = local_object_path(canonical_object_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的文件路径") from exc
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="本地文件不存在")
    return FileResponse(path)


@app.post("/api/uploads/local/{object_key:path}", status_code=204)
async def upload_local_object(object_key: str, request: Request, user: User = Depends(current_user)) -> Response:
    _ = user
    if settings.object_storage_provider != "local":
        raise HTTPException(status_code=404, detail="本地上传仅在 local 存储模式可用")
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    if len(body) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件超过 200MB 限制")
    canonical_object_key = canonical_storage_key(object_key)
    try:
        path = local_object_path(canonical_object_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="无效的文件路径") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return Response(status_code=204)


@app.post("/api/orders/{order_number}/attachments", status_code=201, response_model=OrderEnvelope)
def add_attachment(
    order_number: str,
    input_data: AttachmentInput,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number, Order.owner_user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    attachment = OrderAttachment(
        order_number=order_number,
        uploader_user_id=user.id,
        file_name=input_data.fileName,
        file_size=input_data.fileSize,
        content_type=input_data.contentType,
        bucket=input_data.bucket,
        storage_key=input_data.storageKey,
        checksum=input_data.checksum,
        scan_status="queued",
    )
    db.add(attachment)
    order.last_customer_activity_at = now_iso()
    order.updated_at = now_iso()
    db.commit()
    db.refresh(attachment)
    schedule_attachment_analysis(db, attachment.id)
    db.refresh(order)
    ensure_automation_for_order(db, order, reason="attachment_added")
    return {"order": order_payload(db, order)}


@app.get("/api/orders/{order_number}/attachments/{attachment_id}/download", response_model=AttachmentDownloadEnvelope)
def download_order_attachment(
    order_number: str,
    attachment_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if user.role != "admin" and order.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    attachment = db.query(OrderAttachment).filter(OrderAttachment.order_number == order_number, OrderAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    if user.role != "admin" and attachment.visibility != "public":
        raise HTTPException(status_code=403, detail="不能访问该附件")
    try:
        presign = create_presigned_download(attachment.bucket, attachment.storage_key)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "download": {
            "provider": presign.provider,
            "bucket": presign.bucket,
            "objectKey": presign.object_key,
            "downloadUrl": presign.download_url,
            "expiresIn": presign.expires_in,
        }
    }


@app.get("/api/admin/orders", response_model=AdminOrdersOut)
def admin_orders(
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    service: str | None = Query(default=None),
    assignee: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=100),
) -> dict[str, object]:
    _ = admin
    query = db.query(Order)
    if search:
        like = f"%{search}%"
        attachment_orders = db.query(OrderAttachment.order_number).filter(OrderAttachment.file_name.ilike(like))
        query = query.filter(
            or_(
                Order.order_number.ilike(like),
                Order.customer_name.ilike(like),
                Order.contact.ilike(like),
                Order.category.ilike(like),
                Order.title.ilike(like),
                Order.demand.ilike(like),
                Order.original_demand.ilike(like),
                Order.next_action.ilike(like),
                Order.order_number.in_(attachment_orders),
            )
        )
    if status:
        query = query.filter(Order.status == status)
    if intent:
        query = query.filter(Order.intent == intent)
    if service:
        query = query.filter(Order.service_slug == service)
    if assignee:
        query = query.filter(Order.assigned_admin_id == assignee)
    if tag:
        like = f"%{tag}%"
        query = query.filter(
            or_(
                Order.category.ilike(like),
                Order.service_slug.ilike(like),
                Order.intent.ilike(like),
                Order.priority.ilike(like),
                Order.ai_status.ilike(like),
            )
        )
    total = query.count()
    rows = query.order_by(Order.updated_at.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return {
        "orders": [order_payload(db, row, admin=True) for row in rows],
        "pagination": {"page": page, "pageSize": pageSize, "total": total, "hasMore": page * pageSize < total},
    }


@app.get("/api/admin/orders/{order_number}", response_model=AdminOrderEnvelope)
def admin_order(order_number: str, admin: User = Depends(current_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    _ = admin
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"order": order_payload(db, order, admin=True)}


@app.patch("/api/admin/orders/{order_number}", response_model=AdminOrderEnvelope)
def patch_admin_order(
    order_number: str,
    input_data: AdminOrderPatch,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    before = order.status
    for field, attr in [
        ("status", "status"),
        ("priority", "priority"),
        ("quotedPrice", "quoted_price"),
        ("cost", "cost"),
        ("profit", "profit"),
        ("publicNotes", "public_notes"),
        ("internalNotes", "internal_notes"),
        ("nextAction", "next_action"),
    ]:
        value = getattr(input_data, field)
        if value is not None:
            setattr(order, attr, value)
    order.last_admin_activity_at = now_iso()
    order.updated_at = now_iso()
    db.add(AdminAuditLog(order_number=order_number, actor_user_id=admin.id, action="admin.patch_order", details=input_data.model_dump_json()))
    if before != order.status:
        db.add(OrderEvent(order_number=order_number, status=order.status, note="管理员更新订单状态", created_by=admin.id))
    db.commit()
    db.refresh(order)
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/messages", status_code=201, response_model=AdminOrderEnvelope)
def create_admin_message(
    order_number: str,
    input_data: MessageInput,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    visibility = input_data.visibility if input_data.visibility in {"public", "internal"} else "public"
    message = OrderMessage(order_number=order_number, author_user_id=admin.id, body=input_data.body, visibility=visibility)
    db.add(message)
    db.flush()
    if visibility == "public":
        create_order_message_notification(db, order=order, message=message, actor=admin)
    order.last_admin_activity_at = now_iso()
    order.updated_at = now_iso()
    db.add(AdminAuditLog(order_number=order_number, actor_user_id=admin.id, action="admin.message", details=json.dumps({"visibility": visibility})))
    db.commit()
    db.refresh(order)
    ensure_automation_for_order(db, order, reason="admin_message")
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/suggestions/{suggestion_id}/apply", response_model=AdminOrderEnvelope)
def apply_automation_suggestion(
    order_number: str,
    suggestion_id: str,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    suggestion = (
        db.query(OrderAutomationSuggestion)
        .filter(OrderAutomationSuggestion.id == suggestion_id, OrderAutomationSuggestion.order_number == order_number)
        .first()
    )
    if not order or not suggestion:
        raise HTTPException(status_code=404, detail="建议不存在")
    if suggestion.suggested_status:
        before = order.status
        order.status = suggestion.suggested_status
        order.next_action = suggestion.summary
        order.updated_at = now_iso()
        if before != order.status:
            db.add(OrderEvent(order_number=order_number, status=order.status, note=f"管理员采纳自动化建议：{suggestion.summary}", created_by=admin.id))
    suggestion.status = "applied"
    suggestion.resolved_at = now_iso()
    db.add(
        AdminAuditLog(
            order_number=order_number,
            actor_user_id=admin.id,
            action="automation.apply_suggestion",
            details=json.dumps({"suggestionId": suggestion_id, "suggestedStatus": suggestion.suggested_status}, ensure_ascii=False),
        )
    )
    db.commit()
    db.refresh(order)
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/quotes", status_code=201, response_model=AdminOrderEnvelope)
def create_quote(order_number: str, input_data: QuoteInput, admin: User = Depends(current_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    db.add(Quote(order_number=order_number, amount=input_data.amount, kind=input_data.kind, note=input_data.note, created_by=admin.id))
    order.status = "quoted"
    order.quoted_price = input_data.amount
    order.public_notes = input_data.note
    db.add(OrderEvent(order_number=order_number, status="quoted", note="管理员已发送报价", created_by=admin.id))
    db.commit()
    ensure_automation_for_order(db, order, reason="quote_created")
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/payments", status_code=201, response_model=AdminOrderEnvelope)
def create_payment(order_number: str, input_data: PaymentInput, admin: User = Depends(current_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    db.add(
        PaymentRecord(
            order_number=order_number,
            amount=input_data.amount,
            kind=input_data.kind,
            method=input_data.method,
            status=input_data.status,
            note=input_data.note,
            created_by=admin.id,
        )
    )
    order.status = "in_progress" if input_data.status == "received" else "deposit_pending"
    db.add(OrderEvent(order_number=order_number, status=order.status, note=f"管理员记录付款：{input_data.status}", created_by=admin.id))
    db.commit()
    ensure_automation_for_order(db, order, reason="payment_recorded")
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/deliverables", status_code=201, response_model=AdminOrderEnvelope)
def create_deliverable(
    order_number: str,
    input_data: DeliverableInput,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    db.add(
        Deliverable(
            order_number=order_number,
            title=input_data.title,
            description=input_data.description,
            storage_key=input_data.storageKey,
            created_by=admin.id,
        )
    )
    order.status = "review"
    order.public_notes = "交付物已上传，等待验收。"
    db.add(OrderEvent(order_number=order_number, status="review", note="管理员上传交付物", created_by=admin.id))
    db.commit()
    ensure_automation_for_order(db, order, reason="deliverable_created")
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/automation/run", response_model=AdminOrderEnvelope)
def run_automation(order_number: str, admin: User = Depends(current_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    ensure_automation_for_order(db, order, reason="manual_run")
    db.add(AdminAuditLog(order_number=order_number, actor_user_id=admin.id, action="automation.run", details="{}"))
    db.commit()
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/admin/orders/{order_number}/attachments/{attachment_id}/retry-scan", response_model=AdminOrderEnvelope)
def retry_attachment_scan(
    order_number: str,
    attachment_id: str,
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number).first()
    attachment = db.query(OrderAttachment).filter(OrderAttachment.order_number == order_number, OrderAttachment.id == attachment_id).first()
    if not order or not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    attachment.scan_status = "queued"
    attachment.scan_error = ""
    attachment.retry_count += 1
    db.add(AdminAuditLog(order_number=order_number, actor_user_id=admin.id, action="attachment.retry_scan", details=json.dumps({"attachmentId": attachment_id})))
    db.commit()
    schedule_attachment_analysis(db, attachment.id)
    db.refresh(order)
    return {"order": order_payload(db, order, admin=True)}


@app.post("/api/agent/sessions", status_code=201, response_model=AgentSessionEnvelope)
def create_agent_session(
    input_data: AgentSessionInput,
    user: User | None = Depends(current_user_optional),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = create_xiaoku_session(db, user, input_data.visitorId, input_data.pagePath)
    return {"session": {"id": session.id, "pagePath": session.page_path, "userId": session.user_id}}


@app.post("/api/agent/chat", response_model=AgentChatOut)
def agent_chat(
    input_data: AgentChatInput,
    request: Request,
    user: User | None = Depends(current_user_optional),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = db.get(AgentSession, input_data.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    if session.user_id and (not user or user.id != session.user_id):
        raise HTTPException(status_code=403, detail="不能访问其他用户的小酷会话")
    if not check_agent_rate_limit(db, user=user, visitor_id=session.visitor_id, ip_address=client_ip(request)):
        raise HTTPException(status_code=429, detail="小酷今天被问得有点多，请稍后再试")
    return xiaoku_chat(db, session, input_data.message, user)


@app.get("/api/orders/{order_number}/assistant-summary", response_model=AssistantSummaryOut)
def assistant_summary(order_number: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    order = db.query(Order).filter(Order.order_number == order_number, Order.owner_user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"summary": {"orderNumber": order.order_number, "status": order.status, "nextAction": order.next_action, "publicNotes": order.public_notes}}


def schedule_attachment_analysis(db: Session, attachment_id: str) -> None:
    if settings.app_env in {"local", "dev", "development", "test"}:
        analyze_attachment_sync(db, attachment_id)
    else:
        analyze_attachment.delay(attachment_id)
