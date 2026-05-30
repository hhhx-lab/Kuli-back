import json
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.models.entities import Notification, NotificationEvent, Order, OrderMessage, User
from app.notifications.email import render_template


def create_order_message_notification(
    db: Session,
    *,
    order: Order,
    message: OrderMessage,
    actor: User,
) -> tuple[Notification, NotificationEvent] | None:
    if message.visibility != "public" or not order.owner_user_id:
        return None

    recipient = db.get(User, order.owner_user_id)
    if not recipient:
        return None

    idempotency_key = f"order_message:{message.id}:email"
    existing_event = db.query(NotificationEvent).filter(NotificationEvent.idempotency_key == idempotency_key).first()
    if existing_event and existing_event.notification_id:
        existing_notification = db.get(Notification, existing_event.notification_id)
        if existing_notification:
            return existing_notification, existing_event

    title = "管理员回复了你的订单"
    target_url = f"/orders/{order.order_number}"
    notification = Notification(
        user_id=recipient.id,
        type="order_message",
        order_number=order.order_number,
        title=title,
        body=message.body,
        status="unread",
        target_url=target_url,
        metadata_json=json.dumps({"messageId": message.id, "actorUserId": actor.id}, ensure_ascii=False),
    )
    db.add(notification)
    db.flush()

    event = NotificationEvent(
        event_type="order_message",
        user_id=recipient.id,
        notification_id=notification.id,
        order_number=order.order_number,
        channel="email",
        recipient=recipient.email,
        subject=f"{title} {order.order_number}",
        body=message.body,
        status="pending",
        idempotency_key=idempotency_key,
    )
    db.add(event)
    db.flush()
    return notification, event


def create_email_verification_event(db: Session, *, user: User, token: str, base_url: str) -> NotificationEvent:
    verify_url = f"{base_url.rstrip('/')}/login?verifyToken={quote(token)}"
    event = NotificationEvent(
        event_type="email_verification",
        user_id=user.id,
        channel="email",
        recipient=user.email,
        subject="验证你的酷里邮箱",
        body=render_template("email_verify.html", {"verify_url": verify_url}),
        status="pending",
        idempotency_key=f"email_verification:{user.id}:{token[:12]}",
    )
    db.add(event)
    db.flush()
    return event


def create_password_reset_event(db: Session, *, user: User, token: str, base_url: str) -> NotificationEvent:
    reset_url = f"{base_url.rstrip('/')}/login?resetToken={quote(token)}"
    event = NotificationEvent(
        event_type="password_reset",
        user_id=user.id,
        channel="email",
        recipient=user.email,
        subject="重置你的酷里密码",
        body=render_template("password_reset.html", {"reset_url": reset_url}),
        status="pending",
        idempotency_key=f"password_reset:{user.id}:{token[:12]}",
    )
    db.add(event)
    db.flush()
    return event
