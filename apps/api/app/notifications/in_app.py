from sqlalchemy.orm import Session

from app.models.entities import Notification, now_iso


def serialize_notification(notification: Notification) -> dict[str, object]:
    return {
        "id": notification.id,
        "type": notification.type,
        "orderNumber": notification.order_number,
        "title": notification.title,
        "body": notification.body,
        "status": notification.status,
        "targetUrl": notification.target_url,
        "createdAt": notification.created_at,
        "readAt": notification.read_at,
    }


def list_notifications(db: Session, user_id: str, *, status: str | None = None, limit: int = 50) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if status in {"unread", "read", "archived"}:
        query = query.filter(Notification.status == status)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def unread_count(db: Session, user_id: str) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.status == "unread").count()


def mark_read(db: Session, user_id: str, notification_id: str) -> Notification | None:
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if not notification:
        return None
    if notification.status != "read":
        notification.status = "read"
        notification.read_at = now_iso()
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: str) -> int:
    rows = db.query(Notification).filter(Notification.user_id == user_id, Notification.status == "unread").all()
    timestamp = now_iso()
    for notification in rows:
        notification.status = "read"
        notification.read_at = timestamp
        db.add(notification)
    db.commit()
    return len(rows)
