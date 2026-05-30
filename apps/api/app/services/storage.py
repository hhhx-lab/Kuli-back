from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
from pathlib import Path
import time
from urllib.parse import quote, urlencode, urlparse, urlunparse
from uuid import uuid4

import boto3

from app.core.config import get_settings


@dataclass(frozen=True)
class PresignedUpload:
    bucket: str
    object_key: str
    upload_url: str
    public_url: str | None
    provider: str
    fields: dict[str, str]


@dataclass(frozen=True)
class PresignedDownload:
    bucket: str
    object_key: str
    download_url: str
    provider: str
    expires_in: int


def build_object_key(order_number: str | None, file_name: str) -> str:
    safe_name = quote(file_name.replace("/", "_"))
    prefix = order_number or "draft"
    return f"orders/{prefix}/{uuid4()}-{safe_name}"


def create_presigned_upload(file_name: str, content_type: str, order_number: str | None = None, file_size: int = 0) -> PresignedUpload:
    settings = get_settings()
    object_key = build_object_key(order_number, file_name)
    provider = settings.object_storage_provider
    if provider == "local":
        return PresignedUpload(
            bucket=settings.object_storage_bucket,
            object_key=object_key,
            upload_url=f"/api/uploads/local/{object_key}",
            public_url=None,
            provider=provider,
            fields={"contentType": content_type},
        )

    if provider in {"s3", "r2"}:
        return create_s3_compatible_presigned_upload(object_key, content_type)
    if provider == "oss":
        return create_oss_presigned_upload(object_key, content_type, file_size)
    raise RuntimeError(f"Unsupported object storage provider: {provider}")


def create_s3_compatible_presigned_upload(object_key: str, content_type: str) -> PresignedUpload:
    settings = get_settings()
    bucket = settings.object_storage_bucket
    if not settings.object_storage_access_key_id or not settings.object_storage_secret_access_key:
        raise RuntimeError("Object storage credentials are missing")

    client = boto3.client(
        "s3",
        endpoint_url=settings.object_storage_endpoint or None,
        region_name=settings.object_storage_region,
        aws_access_key_id=settings.object_storage_access_key_id,
        aws_secret_access_key=settings.object_storage_secret_access_key,
    )
    response = client.generate_presigned_post(
        Bucket=bucket,
        Key=object_key,
        Fields={"Content-Type": content_type},
        Conditions=[{"Content-Type": content_type}],
        ExpiresIn=settings.object_storage_presign_expires_seconds,
    )
    public_base = settings.object_storage_public_base_url.rstrip("/")
    return PresignedUpload(
        bucket=bucket,
        object_key=object_key,
        upload_url=response["url"],
        public_url=f"{public_base}/{object_key}" if public_base else None,
        provider=settings.object_storage_provider,
        fields={key: str(value) for key, value in response["fields"].items()},
    )


def create_oss_presigned_upload(object_key: str, content_type: str, file_size: int) -> PresignedUpload:
    settings = get_settings()
    bucket = settings.object_storage_bucket
    _require_object_storage_credentials()
    upload_url = oss_bucket_url(bucket)
    expires_at = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() + settings.object_storage_presign_expires_seconds))
    max_size = file_size if file_size > 0 else 200 * 1024 * 1024
    policy = {
        "expiration": expires_at,
        "conditions": [
            {"bucket": bucket},
            {"key": object_key},
            {"success_action_status": "204"},
            ["eq", "$Content-Type", content_type],
            ["content-length-range", 0, max_size],
        ],
    }
    encoded_policy = base64.b64encode(json.dumps(policy, separators=(",", ":")).encode("utf-8")).decode("ascii")
    signature = base64.b64encode(
        hmac.new(settings.object_storage_secret_access_key.encode("utf-8"), encoded_policy.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")
    public_base = settings.object_storage_public_base_url.rstrip("/") or upload_url
    return PresignedUpload(
        bucket=bucket,
        object_key=object_key,
        upload_url=upload_url,
        public_url=f"{public_base}/{quote(object_key, safe='/')}" if public_base else None,
        provider=settings.object_storage_provider,
        fields={
            "key": object_key,
            "OSSAccessKeyId": settings.object_storage_access_key_id,
            "policy": encoded_policy,
            "Signature": signature,
            "success_action_status": "204",
            "Content-Type": content_type,
        },
    )


def create_presigned_download(bucket: str, object_key: str) -> PresignedDownload:
    settings = get_settings()
    provider = settings.object_storage_provider
    expires_in = settings.object_storage_presign_expires_seconds
    if provider == "local":
        expires = int(time.time()) + expires_in
        signature = sign_local_object_key(object_key, expires)
        return PresignedDownload(
            bucket=bucket,
            object_key=object_key,
            download_url=f"/api/uploads/local/{quote(object_key, safe='/')}?expires={expires}&signature={signature}",
            provider=provider,
            expires_in=expires_in,
        )
    if provider in {"s3", "r2"}:
        return create_s3_compatible_presigned_download(bucket, object_key)
    if provider == "oss":
        return create_oss_presigned_download(bucket, object_key)
    raise RuntimeError(f"Unsupported object storage provider: {provider}")


def create_s3_compatible_presigned_download(bucket: str, object_key: str) -> PresignedDownload:
    settings = get_settings()
    if not settings.object_storage_access_key_id or not settings.object_storage_secret_access_key:
        raise RuntimeError("Object storage credentials are missing")
    client = boto3.client(
        "s3",
        endpoint_url=settings.object_storage_endpoint or None,
        region_name=settings.object_storage_region,
        aws_access_key_id=settings.object_storage_access_key_id,
        aws_secret_access_key=settings.object_storage_secret_access_key,
    )
    download_url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket or settings.object_storage_bucket, "Key": object_key},
        ExpiresIn=settings.object_storage_presign_expires_seconds,
    )
    return PresignedDownload(
        bucket=bucket or settings.object_storage_bucket,
        object_key=object_key,
        download_url=download_url,
        provider=settings.object_storage_provider,
        expires_in=settings.object_storage_presign_expires_seconds,
    )


def create_oss_presigned_download(bucket: str, object_key: str) -> PresignedDownload:
    settings = get_settings()
    _require_object_storage_credentials()
    bucket_name = bucket or settings.object_storage_bucket
    expires = int(time.time()) + settings.object_storage_presign_expires_seconds
    canonical_resource = f"/{bucket_name}/{object_key}"
    string_to_sign = f"GET\n\n\n{expires}\n{canonical_resource}"
    signature = base64.b64encode(
        hmac.new(settings.object_storage_secret_access_key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")
    query = urlencode(
        {
            "OSSAccessKeyId": settings.object_storage_access_key_id,
            "Expires": str(expires),
            "Signature": signature,
        }
    )
    download_url = f"{oss_bucket_url(bucket_name)}/{quote(object_key, safe='/')}?{query}"
    return PresignedDownload(
        bucket=bucket_name,
        object_key=object_key,
        download_url=download_url,
        provider=settings.object_storage_provider,
        expires_in=settings.object_storage_presign_expires_seconds,
    )


def _require_object_storage_credentials() -> None:
    settings = get_settings()
    if not settings.object_storage_access_key_id or not settings.object_storage_secret_access_key:
        raise RuntimeError("Object storage credentials are missing")


def oss_bucket_url(bucket: str) -> str:
    settings = get_settings()
    endpoint = settings.object_storage_endpoint.strip().rstrip("/")
    if not endpoint:
        region = settings.object_storage_region.strip()
        if not region or region == "auto":
            raise RuntimeError("OSS endpoint or region is required")
        host = f"{region}.aliyuncs.com" if region.startswith("oss-") else f"oss-{region}.aliyuncs.com"
        endpoint = f"https://{host}"
    if "://" not in endpoint:
        endpoint = f"https://{endpoint}"
    parsed = urlparse(endpoint)
    if parsed.netloc.startswith(f"{bucket}."):
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
    return urlunparse((parsed.scheme, f"{bucket}.{parsed.netloc}", parsed.path.rstrip("/"), "", "", ""))


def sign_local_object_key(object_key: str, expires: int) -> str:
    secret = get_settings().app_secret_key.encode("utf-8")
    message = f"{object_key}:{expires}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_local_download_signature(object_key: str, expires: int, signature: str) -> bool:
    if expires < int(time.time()):
        return False
    expected = sign_local_object_key(object_key, expires)
    return hmac.compare_digest(expected, signature)


def local_object_path(object_key: str) -> Path:
    settings = get_settings()
    root = Path(settings.object_storage_local_dir).resolve()
    path = (root / object_key).resolve()
    if root != path and root not in path.parents:
        raise ValueError("Invalid local object key")
    return path
