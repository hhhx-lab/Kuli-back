from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entities import Order
from app.services.automation import ensure_automation_for_order
from app.tasks.celery_app import celery_app


@celery_app.task(name="orders.run_automation")
def run_order_automation(order_number: str) -> str:
    with SessionLocal() as db:
        order = db.query(Order).filter(Order.order_number == order_number).first()
        if not order:
            return "missing"
        ensure_automation_for_order(db, order, reason="celery_task")
        return "ok"


def run_order_automation_sync(db: Session, order: Order) -> None:
    ensure_automation_for_order(db, order, reason="sync_task")
