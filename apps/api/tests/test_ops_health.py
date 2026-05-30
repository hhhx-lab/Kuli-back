from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from app.database import configure_database, init_database
from app.main import app
from app.core.config import Settings
from app.services.health import check_llm


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


@pytest.mark.anyio
async def test_health_deps_reports_required_and_degraded_dependencies(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health/deps")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "kuli-api"
    assert body["environment"] == "local"
    assert body["ok"] is True

    deps = body["dependencies"]
    assert deps["database"]["ok"] is True
    assert deps["database"]["required"] is True
    assert deps["database"]["driver"] == "sqlite"

    assert deps["objectStorage"]["ok"] is True
    assert deps["objectStorage"]["provider"] == "local"

    assert deps["redis"]["required"] is False
    assert deps["mail"]["required"] is False
    assert deps["mail"]["status"] == "disabled"

    assert deps["llm"]["ok"] is True
    assert deps["llm"]["status"] in {"local-rules", "configured"}
    assert deps["rag"]["ok"] is True
    assert deps["rag"]["articleCount"] >= 1


def test_llm_health_accepts_openai_alias_configuration() -> None:
    settings = Settings(openai_api_key="sk-test", openai_model="gpt-5.5", llm_provider="local-rules", llm_model="local-rules")

    report = check_llm(settings)

    assert report["ok"] is True
    assert report["status"] == "configured"
    assert report["provider"] == "openai-compatible"
    assert report["model"] == "gpt-5.5"
