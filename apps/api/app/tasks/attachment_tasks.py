from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entities import OrderAttachment, now_iso
from app.services.storage import local_object_path
from app.tasks.celery_app import celery_app


@celery_app.task(name="attachments.analyze")
def analyze_attachment(attachment_id: str, *, retry: bool = False) -> bool:
    with SessionLocal() as db:
        return analyze_attachment_sync(db, attachment_id, retry=retry)


def analyze_attachment_sync(db: Session, attachment_id: str, *, retry: bool = False) -> bool:
    attachment = db.get(OrderAttachment, attachment_id)
    if not attachment:
        return False
    if retry:
        attachment.retry_count += 1

    try:
        summary = summarize_attachment(attachment)
    except Exception as exc:  # noqa: BLE001 - keep scan failures visible without breaking order flow.
        attachment.scan_status = "failed"
        attachment.scan_error = str(exc)
        attachment.last_scanned_at = now_iso()
        db.commit()
        return False

    attachment.parsed_summary = summary
    attachment.scan_status = "metadata_ready"
    attachment.scan_error = ""
    attachment.last_scanned_at = now_iso()
    db.commit()
    return True


def summarize_attachment(attachment: OrderAttachment) -> str:
    size_kb = max(1, round(attachment.file_size / 1024))
    base = f"已登记附件：{attachment.file_name}，约 {size_kb} KB，类型 {attachment.content_type}。"
    if attachment.bucket != "local":
        return base + " 文件位于对象存储，等待后续解析 worker 或 webhook 确认文件内容。"

    try:
        path = local_object_path(attachment.storage_key)
    except ValueError:
        return base + " 本地 storage key 无效，需要管理员重新确认。"

    if not path.exists():
        return base + " 当前仅有 metadata，尚未检测到本地文件内容。"
    if not path.is_file():
        return base + " 本地路径不是可解析文件。"
    if _looks_text(attachment.content_type, path):
        sample = path.read_text(encoding="utf-8", errors="ignore").strip().replace("\n", " ")[:240]
        if sample:
            return base + f" 已读取文本预览：{sample}"
    return base + " 文件已存在，当前版本先完成 metadata 与可访问性确认。"


def _looks_text(content_type: str, path: Path) -> bool:
    suffix = path.suffix.lower()
    return content_type.startswith("text/") or suffix in {".txt", ".md", ".csv", ".json", ".log"}
