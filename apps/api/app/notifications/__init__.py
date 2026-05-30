"""Unified notification helpers for email events and in-app notifications."""

from app.notifications.events import create_order_message_notification
from app.notifications.in_app import list_notifications, mark_all_read, mark_read, unread_count

__all__ = [
    "create_order_message_notification",
    "list_notifications",
    "mark_all_read",
    "mark_read",
    "unread_count",
]
