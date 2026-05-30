from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import SecurityAuditLog, User, now_iso


COMMON_WEAK_PASSWORDS = {"password", "password123", "12345678", "123456789", "qwerty123", "admin123", "letmein123"}
LOGIN_LOCK_FAILURES = 5
LOGIN_LOCK_MINUTES = 15
REGISTER_IP_LIMIT = 3
REGISTER_IP_WINDOW_SECONDS = 10 * 60
AGENT_VISITOR_DAILY_LIMIT = 5
AGENT_USER_DAILY_LIMIT = 40


@dataclass
class WindowCounter:
    count: int = 0
    reset_at: float = 0


@dataclass
class MemoryRateLimiter:
    buckets: dict[str, WindowCounter] = field(default_factory=dict)

    def hit(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.time()
        bucket = self.buckets.get(key)
        if not bucket or bucket.reset_at <= now:
            bucket = WindowCounter(count=0, reset_at=now + window_seconds)
            self.buckets[key] = bucket
        bucket.count += 1
        return bucket.count <= limit

    def reset(self) -> None:
        self.buckets.clear()


rate_limiter = MemoryRateLimiter()


def reset_security_rate_limits() -> None:
    rate_limiter.reset()


def client_ip(request: Any) -> str:
    forwarded = request.headers.get("x-forwarded-for") if request else None
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or "unknown"
    if request and request.client:
        return request.client.host
    return "unknown"


def validate_password(email: str, password: str) -> str | None:
    lowered = password.lower().strip()
    email_lowered = email.lower().strip()
    if len(password) < 8:
        return "密码至少需要 8 位"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "密码必须同时包含字母和数字"
    if lowered == email_lowered or lowered == email_lowered.split("@", 1)[0]:
        return "密码不能使用邮箱或邮箱前缀"
    if lowered in COMMON_WEAK_PASSWORDS:
        return "密码过于常见，请换一个更安全的密码"
    return None


def check_register_rate_limit(db: Session, ip_address: str) -> bool:
    allowed = rate_limiter.hit(f"register:{ip_address}", limit=REGISTER_IP_LIMIT, window_seconds=REGISTER_IP_WINDOW_SECONDS)
    if not allowed:
        record_security_event(db, action="auth.register.rate_limited", ip_address=ip_address)
        db.commit()
    return allowed


def check_agent_rate_limit(db: Session, *, user: User | None, visitor_id: str | None, ip_address: str) -> bool:
    if user:
        allowed = rate_limiter.hit(f"agent:user:{user.id}", limit=AGENT_USER_DAILY_LIMIT, window_seconds=24 * 60 * 60)
    else:
        key = visitor_id or ip_address
        allowed = rate_limiter.hit(f"agent:visitor:{key}", limit=AGENT_VISITOR_DAILY_LIMIT, window_seconds=24 * 60 * 60)
    if not allowed:
        record_security_event(
            db,
            action="agent.chat.rate_limited",
            user_id=user.id if user else None,
            ip_address=ip_address,
            visitor_id=visitor_id,
        )
        db.commit()
    return allowed


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_locked(user: User) -> bool:
    locked_until = parse_iso(user.locked_until)
    if not locked_until:
        return False
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    return locked_until > datetime.now(timezone.utc)


def record_failed_login(db: Session, user: User | None, *, email: str, ip_address: str) -> None:
    if user:
        user.failed_login_count += 1
        if user.failed_login_count >= LOGIN_LOCK_FAILURES:
            user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LOCK_MINUTES)).isoformat()
            record_security_event(db, action="auth.login.locked", user_id=user.id, email=email, ip_address=ip_address)
    record_security_event(db, action="auth.login.failed", user_id=user.id if user else None, email=email, ip_address=ip_address)
    db.commit()


def record_successful_login(db: Session, user: User) -> None:
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        db.commit()


def record_security_event(
    db: Session,
    *,
    action: str,
    user_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    visitor_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        SecurityAuditLog(
            user_id=user_id,
            email=email or "",
            ip_address=ip_address or "",
            visitor_id=visitor_id or "",
            action=action,
            details=json.dumps(details or {}, ensure_ascii=False),
            created_at=now_iso(),
        )
    )
