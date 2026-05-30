from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import EmailVerificationToken, PasswordResetToken, User, now_iso


def issue_email_verification_token(db: Session, *, user: User, ip_address: str) -> tuple[str, EmailVerificationToken]:
    token = secrets.token_urlsafe(32)
    row = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_auth_token(token),
        expires_at=_expires_at(get_settings().email_verify_token_expire_minutes),
        created_ip=ip_address,
    )
    db.add(row)
    db.flush()
    return token, row


def issue_password_reset_token(db: Session, *, user: User, ip_address: str) -> tuple[str, PasswordResetToken]:
    token = secrets.token_urlsafe(32)
    row = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_auth_token(token),
        expires_at=_expires_at(get_settings().password_reset_token_expire_minutes),
        created_ip=ip_address,
    )
    db.add(row)
    db.flush()
    return token, row


def find_active_email_verification_token(db: Session, token: str) -> EmailVerificationToken | None:
    row = db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == hash_auth_token(token)).first()
    return row if row and _is_active(row.expires_at, row.used_at) else None


def find_active_password_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_auth_token(token)).first()
    return row if row and _is_active(row.expires_at, row.used_at) else None


def hash_auth_token(token: str) -> str:
    secret = get_settings().app_secret_key.encode("utf-8")
    return hmac.new(secret, token.encode("utf-8"), hashlib.sha256).hexdigest()


def mark_token_used(row: EmailVerificationToken | PasswordResetToken) -> None:
    row.used_at = now_iso()


def _expires_at(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def _is_active(expires_at: str, used_at: str | None) -> bool:
    if used_at:
        return False
    try:
        expires = datetime.fromisoformat(expires_at)
    except ValueError:
        return False
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)
