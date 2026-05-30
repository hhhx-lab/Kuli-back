from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "kuli_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.attachment_tasks",
        "app.tasks.embedding_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.order_automation_tasks",
    ],
)
celery_app.conf.update(task_always_eager=settings.app_env == "test", task_serializer="json", result_serializer="json")
