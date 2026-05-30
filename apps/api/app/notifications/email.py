from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import NotificationEvent, now_iso

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_template(name: str, context: dict[str, str]) -> str:
    template = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


def send_email_event(db: Session, event_id: str) -> NotificationEvent | None:
    event = db.get(NotificationEvent, event_id)
    if not event or event.channel != "email":
        return event

    settings = get_settings()
    if not settings.mail_provider:
        event.status = "failed"
        event.retry_count += 1
        event.last_error = "MAIL_PROVIDER 未配置"
        event.updated_at = now_iso()
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # First release keeps provider integration behind one boundary. Sandbox/log/smtp
    # providers can share this success path until a real sender is plugged in.
    event.status = "sent"
    event.last_error = ""
    event.updated_at = now_iso()
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
