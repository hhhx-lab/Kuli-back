import base64
import json
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app import database
from app.core.config import get_settings
from app.database import configure_database, init_database
from app.main import app
from app.models.entities import KnowledgeEmbedding
from app.services.storage import create_presigned_download, create_presigned_upload, local_object_path


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


@pytest.mark.anyio
async def test_public_registration_profile_summary_referral_and_order_gate(client: httpx.AsyncClient) -> None:
    unauth_order = await client.post(
        "/api/orders",
        json={
            "serviceSlug": "not-sure",
            "demand": "我想先问问能不能做一个网页 demo",
            "category": "先聊聊",
            "contact": "guest@example.com",
        },
    )
    assert unauth_order.status_code == 401

    inviter = await client.post(
        "/api/auth/register",
        json={"email": "inviter@example.com", "password": "Invite123!", "displayName": "邀请人", "role": "admin"},
    )
    assert inviter.status_code == 201
    inviter_body = inviter.json()
    assert inviter_body["user"]["role"] == "user"
    inviter_token = inviter_body["token"]

    profile = await client.get("/api/me/profile", headers={"Authorization": f"Bearer {inviter_token}"})
    assert profile.status_code == 200
    assert profile.json()["profile"]["email"] == "inviter@example.com"
    assert profile.json()["profile"]["displayName"] == "邀请人"
    assert profile.json()["profile"]["points"] == 0
    assert profile.json()["profile"]["referralCode"]

    referral_code = profile.json()["profile"]["referralCode"]
    invited = await client.post(
        "/api/auth/register",
        json={"email": "invited@example.com", "password": "Invite456!", "displayName": "被邀请人", "referralCode": referral_code},
    )
    assert invited.status_code == 201

    referral = await client.get("/api/me/referral", headers={"Authorization": f"Bearer {inviter_token}"})
    assert referral.status_code == 200
    assert referral.json()["referral"]["referralCode"] == referral_code
    assert referral.json()["referral"]["rewardedInvites"] == 1
    assert referral.json()["referral"]["points"] == 20

    updated_profile = await client.patch(
        "/api/me/profile",
        headers={"Authorization": f"Bearer {inviter_token}"},
        json={"displayName": "酷里邀请人"},
    )
    assert updated_profile.status_code == 200
    assert updated_profile.json()["profile"]["displayName"] == "酷里邀请人"

    create_order = await client.post(
        "/api/orders",
        headers={"Authorization": f"Bearer {inviter_token}"},
        json={
            "serviceSlug": "tool-development",
            "demand": "我想做一个公开注册后的订单测试",
            "category": "小工具开发",
            "contact": "inviter@example.com",
        },
    )
    assert create_order.status_code == 201
    assert create_order.json()["order"]["customerName"] == "酷里邀请人"

    summary = await client.get("/api/me/summary", headers={"Authorization": f"Bearer {inviter_token}"})
    assert summary.status_code == 200
    assert summary.json()["summary"]["orders"]["total"] == 1
    assert summary.json()["summary"]["orders"]["byStatus"]["submitted"] == 1
    assert summary.json()["summary"]["recentOrders"][0]["orderNumber"] == create_order.json()["order"]["orderNumber"]


@pytest.mark.anyio
async def test_services_and_polish(client: httpx.AsyncClient) -> None:
    services = await client.get("/api/services")
    assert services.status_code == 200
    assert any(item["slug"] == "not-sure" for item in services.json()["services"])

    polish = await client.post("/api/ai/polish-demand", json={"demand": "PDF 翻译一下，格式别乱", "serviceSlug": "document-processing"})
    assert polish.status_code == 200
    assert polish.json()["intent"] in {"consultation", "quote_request", "ready_to_start"}
    assert "polishedDemand" in polish.json()

    knowledge = await client.get("/api/knowledge/search", params={"q": "PDF 翻译"})
    assert knowledge.status_code == 200
    assert knowledge.json()["articles"][0]["source"].startswith("service:")

    public_knowledge = await client.get("/api/knowledge")
    assert public_knowledge.status_code == 200
    sources = {item["source"] for item in public_knowledge.json()["articles"]}
    assert "rule:payment-boundary" in sources
    assert "safety:xiaoku-boundary" in sources

    pricing_rule = await client.get("/api/knowledge/search", params={"q": "定金 收费"})
    assert pricing_rule.status_code == 200
    assert any(item["source"] == "rule:payment-boundary" for item in pricing_rule.json()["articles"])

    with database.SessionLocal() as db:
        embeddings = db.query(KnowledgeEmbedding).all()
        assert embeddings
        assert all(item.embedding_json != "[]" for item in embeddings)
        assert all(item.embedding_vector for item in embeddings)


@pytest.mark.anyio
async def test_docs_center_reads_required_markdown_documents(client: httpx.AsyncClient) -> None:
    docs = await client.get("/api/docs")
    assert docs.status_code == 200
    items = docs.json()["docs"]
    assert [item["slug"] for item in items] == ["quick-start", "concepts", "faq", "guides", "contact"]
    assert all(item["title"] and item["description"] and item["updatedAt"] for item in items)
    assert {item["status"] for item in items} == {"published"}

    quick_start = await client.get("/api/docs/quick-start")
    assert quick_start.status_code == 200
    document = quick_start.json()["doc"]
    assert document["slug"] == "quick-start"
    assert "写小纸条" in document["content"]
    assert any(anchor["id"] == "write-note" for anchor in document["anchors"])
    assert any(item["slug"] == "guides" for item in document["relatedDocs"])

    search = await client.get("/api/docs/search", params={"q": "定金"})
    assert search.status_code == 200
    assert any(result["slug"] in {"concepts", "faq"} for result in search.json()["results"])

    missing = await client.get("/api/docs/missing")
    assert missing.status_code == 404


@pytest.mark.anyio
async def test_auth_and_user_order_isolation(client: httpx.AsyncClient) -> None:
    demo_token = await login(client, "demo@kuli.local", "KuliUser123!")
    other_token = await login(client, "other@kuli.local", "KuliOther123!")

    demo_orders = await client.get("/api/orders", headers={"Authorization": f"Bearer {demo_token}"})
    assert demo_orders.status_code == 200
    assert [order["orderNumber"] for order in demo_orders.json()["orders"]] == ["KULI-DEMO-001"]

    forbidden = await client.get("/api/orders/KULI-DEMO-001", headers={"Authorization": f"Bearer {other_token}"})
    assert forbidden.status_code == 404

    presign = await client.post(
        "/api/uploads/presign",
        headers={"Authorization": f"Bearer {demo_token}"},
        json={"orderNumber": "KULI-DEMO-001", "fileName": "需求截图.png", "fileSize": 128, "contentType": "image/png"},
    )
    assert presign.status_code == 201
    upload = presign.json()["upload"]
    assert upload["objectKey"].startswith("orders/KULI-DEMO-001/")
    uploaded_bytes = b"fake png bytes"
    local_upload = await client.post(
        upload["uploadUrl"],
        headers={"Authorization": f"Bearer {demo_token}", "Content-Type": "image/png"},
        content=uploaded_bytes,
    )
    assert local_upload.status_code == 204
    uploaded_path = local_object_path(upload["objectKey"])
    assert uploaded_path.read_bytes() == uploaded_bytes

    attachment = await client.post(
        "/api/orders/KULI-DEMO-001/attachments",
        headers={"Authorization": f"Bearer {demo_token}"},
        json={
            "fileName": "需求截图.png",
            "fileSize": 128,
            "contentType": "image/png",
            "storageKey": upload["objectKey"],
            "bucket": upload["bucket"],
        },
    )
    assert attachment.status_code == 201
    attachment_id = attachment.json()["order"]["attachments"][0]["id"]
    assert attachment.json()["order"]["attachments"][0]["scanStatus"] == "metadata_ready"
    assert "需求截图.png" in attachment.json()["order"]["attachments"][0]["parsedSummary"]

    download = await client.get(
        f"/api/orders/KULI-DEMO-001/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {demo_token}"},
    )
    assert download.status_code == 200
    assert download.json()["download"]["downloadUrl"].startswith("/api/uploads/local/orders/KULI-DEMO-001/")
    downloaded_file = await client.get(download.json()["download"]["downloadUrl"])
    assert downloaded_file.status_code == 200
    assert downloaded_file.content == uploaded_bytes

    forbidden_download = await client.get(
        f"/api/orders/KULI-DEMO-001/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_download.status_code == 404

    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    admin_download = await client.get(
        f"/api/orders/KULI-DEMO-001/attachments/{attachment_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_download.status_code == 200
    assert admin_download.json()["download"]["expiresIn"] == 3600

    retry = await client.post(
        f"/api/admin/orders/KULI-DEMO-001/attachments/{attachment_id}/retry-scan",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert retry.status_code == 200
    retried_attachment = retry.json()["order"]["attachments"][0]
    assert retried_attachment["scanStatus"] == "metadata_ready"
    assert retried_attachment["retryCount"] == 1

    attachment_search = await client.get(
        "/api/admin/orders",
        params={"search": "需求截图", "pageSize": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert attachment_search.status_code == 200
    assert attachment_search.json()["orders"][0]["orderNumber"] == "KULI-DEMO-001"
    assert attachment_search.json()["pagination"]["total"] == 1
    uploaded_path.unlink(missing_ok=True)


def test_oss_presigned_upload_and_download(monkeypatch) -> None:
    monkeypatch.setenv("OBJECT_STORAGE_PROVIDER", "oss")
    monkeypatch.setenv("OBJECT_STORAGE_ENDPOINT", "https://oss-cn-hangzhou.aliyuncs.com")
    monkeypatch.setenv("OBJECT_STORAGE_BUCKET", "kuli-order-files")
    monkeypatch.setenv("OBJECT_STORAGE_ACCESS_KEY_ID", "oss-access-key")
    monkeypatch.setenv("OBJECT_STORAGE_SECRET_ACCESS_KEY", "oss-secret")
    monkeypatch.setenv("OBJECT_STORAGE_PRESIGN_EXPIRES_SECONDS", "1800")
    get_settings.cache_clear()
    try:
        upload = create_presigned_upload("需求截图.png", "image/png", "KULI-DEMO-001", 128)

        assert upload.provider == "oss"
        assert upload.bucket == "kuli-order-files"
        assert upload.upload_url == "https://kuli-order-files.oss-cn-hangzhou.aliyuncs.com"
        assert upload.fields["key"] == upload.object_key
        assert upload.fields["OSSAccessKeyId"] == "oss-access-key"
        assert upload.fields["success_action_status"] == "204"
        assert upload.fields["Content-Type"] == "image/png"
        policy = json.loads(base64.b64decode(upload.fields["policy"]).decode("utf-8"))
        assert {"bucket": "kuli-order-files"} in policy["conditions"]
        assert {"key": upload.object_key} in policy["conditions"]
        assert ["eq", "$Content-Type", "image/png"] in policy["conditions"]
        assert ["content-length-range", 0, 128] in policy["conditions"]

        download = create_presigned_download(upload.bucket, upload.object_key)
        parsed = urlparse(download.download_url)
        query = parse_qs(parsed.query)
        assert download.provider == "oss"
        assert parsed.netloc == "kuli-order-files.oss-cn-hangzhou.aliyuncs.com"
        assert query["OSSAccessKeyId"] == ["oss-access-key"]
        assert query["Expires"]
        assert query["Signature"]
    finally:
        get_settings.cache_clear()


@pytest.mark.anyio
async def test_public_inquiry_generates_automation_and_admin_search(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/inquiries",
        json={
            "serviceSlug": "not-sure",
            "demand": "我有个表格和截图，不确定能不能做，想先问问报价",
            "category": "先聊聊",
            "contact": "guest@example.com",
        },
    )
    assert response.status_code == 201
    order_number = response.json()["order"]["orderNumber"]
    assert response.json()["order"]["intent"] == "consultation"

    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    admin_orders = await client.get("/api/admin/orders", params={"search": "guest@example.com"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_orders.status_code == 200
    assert admin_orders.json()["orders"][0]["orderNumber"] == order_number
    assert admin_orders.json()["pagination"]["page"] == 1
    assert "internalNotes" in admin_orders.json()["orders"][0]


@pytest.mark.anyio
async def test_admin_workflow_and_xiaoku_boundaries(client: httpx.AsyncClient) -> None:
    admin_token = await login(client, "admin@kuli.local", "KuliAdmin123!")
    run = await client.post("/api/admin/orders/KULI-DEMO-001/automation/run", headers={"Authorization": f"Bearer {admin_token}"})
    assert run.status_code == 200
    detail = await client.get("/api/admin/orders/KULI-DEMO-001", headers={"Authorization": f"Bearer {admin_token}"})
    assert detail.status_code == 200
    suggestion_id = detail.json()["order"]["automationSuggestions"][0]["id"]
    applied = await client.post(
        f"/api/admin/orders/KULI-DEMO-001/suggestions/{suggestion_id}/apply",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert applied.status_code == 200

    quote = await client.post(
        "/api/admin/orders/KULI-DEMO-001/quotes",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"amount": 300, "kind": "deposit", "note": "先收定金后开始制作"},
    )
    assert quote.status_code == 201
    assert quote.json()["order"]["status"] == "quoted"
    assert quote.json()["order"]["quotes"][0]["amount"] == 300

    message = await client.post(
        "/api/admin/orders/KULI-DEMO-001/messages",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"body": "我先公开追问一下截止时间", "visibility": "public"},
    )
    assert message.status_code == 201
    assert message.json()["order"]["messages"][-1]["visibility"] == "public"

    payment = await client.post(
        "/api/admin/orders/KULI-DEMO-001/payments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"amount": 300, "kind": "deposit", "method": "manual", "status": "received"},
    )
    assert payment.status_code == 201

    deliverable = await client.post(
        "/api/admin/orders/KULI-DEMO-001/deliverables",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "演示包", "description": "首版 demo", "storageKey": "orders/KULI-DEMO-001/demo.zip"},
    )
    assert deliverable.status_code == 201
    assert deliverable.json()["order"]["status"] == "review"

    demo_token = await login(client, "demo@kuli.local", "KuliUser123!")
    accept = await client.post("/api/orders/KULI-DEMO-001/accept", headers={"Authorization": f"Bearer {demo_token}"})
    assert accept.status_code == 200
    assert accept.json()["order"]["status"] == "completed"

    session = await client.post("/api/agent/sessions", headers={"Authorization": f"Bearer {demo_token}"}, json={"pagePath": "/orders"})
    assert session.status_code == 201
    chat = await client.post(
        "/api/agent/chat",
        headers={"Authorization": f"Bearer {demo_token}"},
        json={"sessionId": session.json()["session"]["id"], "message": "我的订单现在到哪一步了？"},
    )
    assert chat.status_code == 200
    assert "成本" not in chat.json()["answer"]
    assert "KULI-DEMO-001" in chat.json()["answer"]
