from app.database import SessionLocal
from app.notifications.email import send_email_event
from app.tasks.celery_app import celery_app


def send_notification_event_sync(event_id: str) -> str | None:
    with SessionLocal() as db:
        event = send_email_event(db, event_id)
        return event.status if event else None


@celery_app.task(name="notifications.send_event")
def send_notification_event(event_id: str) -> str | None:
    return send_notification_event_sync(event_id)
