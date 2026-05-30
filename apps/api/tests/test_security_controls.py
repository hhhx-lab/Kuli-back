from collections.abc import AsyncIterator
from pathlib import Path
import re

import httpx
import pytest
from sqlalchemy import text

from app import database
from app.database import configure_database, init_database
from app.main import app
from app.models.entities import User


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    configure_database(f"sqlite:///{tmp_path / 'test.db'}")
    init_database()
    transport = httpx.ASGITransport(app=app, client=("203.0.113.10", 443))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def security_actions() -> list[str]:
    with database.SessionLocal() as db:
        rows = db.execute(text("select action from security_audit_logs order by created_at asc")).all()
        return [row[0] for row in rows]


def latest_email_event(event_type: str, recipient: str) -> dict[str, object]:
    with database.SessionLocal() as db:
        row = db.execute(
            text(
                """
                select event_type, recipient, subject, body, status
                from notification_events
                where event_type = :event_type and recipient = :recipient
                order by created_at desc
                limit 1
                """
            ),
            {"event_type": event_type, "recipient": recipient},
        ).mappings().first()
        assert row
        return dict(row)


def token_from_event_body(body: str) -> str:
    match = re.search(r"(?:verifyToken|resetToken|token)=([^\"'&<\s]+)", body)
    assert match, body
    return match.group(1)


@pytest.mark.anyio
async def test_registration_rejects_weak_passwords_and_records_security_audit(client: httpx.AsyncClient) -> None:
    weak = await client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "password", "displayName": "弱密码"},
    )
    assert weak.status_code == 422
    assert "密码" in weak.json()["detail"]

    email_as_password = await client.post(
        "/api/auth/register",
        json={"email": "same@example.com", "password": "same@example.com", "displayName": "邮箱当密码"},
    )
    assert email_as_password.status_code == 422

    with database.SessionLocal() as db:
        assert db.query(User).filter(User.email == "weak@example.com").first() is None

    assert "auth.register.weak_password" in security_actions()


@pytest.mark.anyio
async def test_failed_login_locks_account_without_revealing_email_existence(client: httpx.AsyncClient) -> None:
    for _ in range(5):
        failure = await client.post("/api/auth/login", json={"email": "demo@kuli.local", "password": "wrong-password"})
        assert failure.status_code == 401
        assert failure.json()["detail"] == "邮箱或密码不正确"

    locked = await client.post("/api/auth/login", json={"email": "demo@kuli.local", "password": "KuliUser123!"})
    assert locked.status_code == 423
    assert locked.json()["detail"] == "登录尝试过多，请稍后再试"

    unknown = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == "邮箱或密码不正确"

    actions = security_actions()
    assert actions.count("auth.login.failed") >= 5
    assert "auth.login.locked" in actions


@pytest.mark.anyio
async def test_registration_and_agent_chat_are_rate_limited_per_ip_or_visitor(client: httpx.AsyncClient) -> None:
    for index in range(3):
        created = await client.post(
            "/api/auth/register",
            json={"email": f"burst-{index}@example.com", "password": f"BurstPass{index}9", "displayName": f"Burst {index}"},
        )
        assert created.status_code == 201

    limited_register = await client.post(
        "/api/auth/register",
        json={"email": "burst-locked@example.com", "password": "BurstPass99", "displayName": "Too Many"},
    )
    assert limited_register.status_code == 429
    assert limited_register.json()["detail"] == "注册请求过于频繁，请稍后再试"

    session = await client.post("/api/agent/sessions", json={"pagePath": "/", "visitorId": "visitor-rate-limit"})
    assert session.status_code == 201
    for _ in range(5):
        ok = await client.post(
            "/api/agent/chat",
            json={"sessionId": session.json()["session"]["id"], "message": "你们能帮我做什么？"},
        )
        assert ok.status_code == 200

    limited_chat = await client.post(
        "/api/agent/chat",
        json={"sessionId": session.json()["session"]["id"], "message": "还能继续问吗？"},
    )
    assert limited_chat.status_code == 429
    assert limited_chat.json()["detail"] == "小酷今天被问得有点多，请稍后再试"

    actions = security_actions()
    assert "auth.register.rate_limited" in actions
    assert "agent.chat.rate_limited" in actions


@pytest.mark.anyio
async def test_email_verification_request_and_confirm_updates_current_user(client: httpx.AsyncClient) -> None:
    login = await client.post("/api/auth/login", json={"email": "demo@kuli.local", "password": "KuliUser123!"})
    assert login.status_code == 200
    token = login.json()["token"]

    request = await client.post("/api/auth/email-verification/request", headers={"Authorization": f"Bearer {token}"})
    assert request.status_code == 202
    assert request.json()["ok"] is True

    event = latest_email_event("email_verification", "demo@kuli.local")
    assert event["status"] == "pending"
    assert "验证" in str(event["subject"])

    verify_token = token_from_event_body(str(event["body"]))
    confirm = await client.post("/api/auth/email-verification/confirm", json={"token": verify_token})
    assert confirm.status_code == 200
    assert confirm.json()["ok"] is True

    profile = await client.get("/api/me/profile", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["profile"]["emailVerifiedAt"]

    reused = await client.post("/api/auth/email-verification/confirm", json={"token": verify_token})
    assert reused.status_code == 400
    assert "无效" in reused.json()["detail"]

    actions = security_actions()
    assert "auth.email_verification.requested" in actions
    assert "auth.email_verification.confirmed" in actions


@pytest.mark.anyio
async def test_password_reset_does_not_reveal_email_and_rotates_password(client: httpx.AsyncClient) -> None:
    request = await client.post("/api/auth/password-reset/request", json={"email": "demo@kuli.local"})
    assert request.status_code == 202
    assert request.json()["ok"] is True

    unknown = await client.post("/api/auth/password-reset/request", json={"email": "missing@example.com"})
    assert unknown.status_code == 202
    assert unknown.json() == request.json()

    event = latest_email_event("password_reset", "demo@kuli.local")
    assert event["status"] == "pending"
    assert "重置" in str(event["subject"])

    reset_token = token_from_event_body(str(event["body"]))
    weak = await client.post("/api/auth/password-reset/confirm", json={"token": reset_token, "password": "password"})
    assert weak.status_code == 422

    confirm = await client.post("/api/auth/password-reset/confirm", json={"token": reset_token, "password": "KuliUser456!"})
    assert confirm.status_code == 200
    assert confirm.json()["ok"] is True

    old_login = await client.post("/api/auth/login", json={"email": "demo@kuli.local", "password": "KuliUser123!"})
    assert old_login.status_code == 401

    new_login = await client.post("/api/auth/login", json={"email": "demo@kuli.local", "password": "KuliUser456!"})
    assert new_login.status_code == 200

    reused = await client.post("/api/auth/password-reset/confirm", json={"token": reset_token, "password": "KuliUser789!"})
    assert reused.status_code == 400

    actions = security_actions()
    assert "auth.password_reset.requested" in actions
    assert "auth.password_reset.confirmed" in actions
