import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_urlsafe(18)
    iterations = 120_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations, dklen=32)
    return f"pbkdf2${iterations}${salt}${base64.urlsafe_b64encode(digest).decode('utf-8')}"


def verify_password(password: str, verifier: str) -> bool:
    try:
        scheme, iterations_text, salt, expected = verifier.split("$", 3)
        if scheme != "pbkdf2":
            return False
        iterations = int(iterations_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations, dklen=32)
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode("utf-8"), expected)
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _unb64(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def sign_token(payload: dict[str, Any], ttl_seconds: int | None = None) -> str:
    settings = get_settings()
    expires_in = ttl_seconds or settings.access_token_expire_minutes * 60
    body = {**payload, "exp": int(time.time()) + expires_in}
    encoded = _b64(json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signature = hmac.new(settings.app_secret_key.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).digest()
    return f"{encoded}.{_b64(signature)}"


def verify_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        encoded, signature = token.split(".", 1)
        expected = _b64(hmac.new(settings.app_secret_key.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_unb64(encoded).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
