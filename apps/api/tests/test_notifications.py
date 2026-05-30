from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app import database
from app.database import configure_database, init_database
from app.main import app


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    configure_database(f"sqlite:///{tmp_path / 'test.db'}")
    init_database()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def notification_events(order_number: str) -> list[dict[str, object]]:
    with database.SessionLocal() as db:
        rows = db.execute(
            text(
                """
                select id, order_number, channel, recipient, subject, body, status, retry_count, last_error
                from notification_events
                where order_number = :order_number
                order by created_at asc
                """
            ),
            {"order_number": order_number},
        ).mappings()
        return [dict(row) for row in rows]


@pytest.mark.anyio
async def test_admin_public_reply_creates_email_event_and_in_app_notification(client: httpx.AsyncClient) -> None:
    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    demo_token = await login(client, "demo@kuli.local", "KuliUser123!")
    other_token = await login(client, "other@kuli.local", "KuliOther123!")

    reply = await client.post(
        "/api/admin/orders/KULI-DEMO-001/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"body": "请补充一下最终希望交付的页面数量。", "visibility": "public"},
    )
    assert reply.status_code == 201

    events = notification_events("KULI-DEMO-001")
    assert len(events) == 1
    assert events[0]["channel"] == "email"
    assert events[0]["recipient"] == "demo@kuli.local"
    assert events[0]["status"] == "pending"
    assert "管理员回复" in str(events[0]["subject"])

    unread = await client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {demo_token}"})
    assert unread.status_code == 200
    assert unread.json()["unreadCount"] == 1

    listing = await client.get("/api/notifications", headers={"Authorization": f"Bearer {demo_token}"})
    assert listing.status_code == 200
    notifications = listing.json()["notifications"]
    assert len(notifications) == 1
    assert notifications[0]["type"] == "order_message"
    assert notifications[0]["status"] == "unread"
    assert notifications[0]["orderNumber"] == "KULI-DEMO-001"
    assert notifications[0]["targetUrl"] == "/orders/KULI-DEMO-001"
    assert "页面数量" in notifications[0]["body"]

    other_listing = await client.get("/api/notifications", headers={"Authorization": f"Bearer {other_token}"})
    assert other_listing.status_code == 200
    assert other_listing.json()["notifications"] == []

    notification_id = notifications[0]["id"]
    read = await client.patch(f"/api/notifications/{notification_id}/read", headers={"Authorization": f"Bearer {demo_token}"})
    assert read.status_code == 200
    assert read.json()["notification"]["status"] == "read"

    unread_after_read = await client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {demo_token}"})
    assert unread_after_read.status_code == 200
    assert unread_after_read.json()["unreadCount"] == 0

    forbidden = await client.patch(f"/api/notifications/{notification_id}/read", headers={"Authorization": f"Bearer {other_token}"})
    assert forbidden.status_code == 404


@pytest.mark.anyio
async def test_internal_admin_reply_does_not_notify_customer_and_read_all_marks_visible_items(client: httpx.AsyncClient) -> None:
    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    demo_token = await login(client, "demo@kuli.local", "KuliUser123!")

    internal = await client.post(
        "/api/admin/orders/KULI-DEMO-001/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"body": "内部备注：先估算成本，不要发给客户。", "visibility": "internal"},
    )
    assert internal.status_code == 201
    assert notification_events("KULI-DEMO-001") == []

    for body in ["第一条公开提醒", "第二条公开提醒"]:
        response = await client.post(
            "/api/admin/orders/KULI-DEMO-001/messages",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"body": body, "visibility": "public"},
        )
        assert response.status_code == 201

    unread = await client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {demo_token}"})
    assert unread.status_code == 200
    assert unread.json()["unreadCount"] == 2

    read_all = await client.patch("/api/notifications/read-all", headers={"Authorization": f"Bearer {demo_token}"})
    assert read_all.status_code == 200
    assert read_all.json()["updated"] == 2

    unread_after = await client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {demo_token}"})
    assert unread_after.status_code == 200
    assert unread_after.json()["unreadCount"] == 0


@pytest.mark.anyio
async def test_mail_worker_failure_keeps_in_app_notification_visible(client: httpx.AsyncClient) -> None:
    from app.tasks.notification_tasks import send_notification_event_sync

    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    demo_token = await login(client, "demo@kuli.local", "KuliUser123!")

    reply = await client.post(
        "/api/admin/orders/KULI-DEMO-001/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"body": "邮件失败也应该能在站内看到。", "visibility": "public"},
    )
    assert reply.status_code == 201
    event_id = str(notification_events("KULI-DEMO-001")[0]["id"])

    status = send_notification_event_sync(event_id)
    assert status == "failed"

    events = notification_events("KULI-DEMO-001")
    assert events[0]["status"] == "failed"
    assert events[0]["retry_count"] == 1
    assert "MAIL_PROVIDER" in str(events[0]["last_error"])

    listing = await client.get("/api/notifications", headers={"Authorization": f"Bearer {demo_token}"})
    assert listing.status_code == 200
    assert listing.json()["notifications"][0]["status"] == "unread"
    assert "邮件失败" in listing.json()["notifications"][0]["body"]
