import hashlib
import importlib.util
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))
os.environ["DEPLOYMENT_MODE"] = "offline"
os.environ["API_HOST"] = "127.0.0.1"


@pytest.fixture(autouse=True)
def isolated_local_storage(tmp_path, monkeypatch):
    from gateway.providers.hub import reset_provider_hub
    from gateway.storage.offline_db import close_offline_db, init_offline_db

    close_offline_db()
    reset_provider_hub()
    monkeypatch.setenv("FLYTO_OFFLINE_DB_PATH", str(tmp_path / "flow.db"))
    monkeypatch.setenv("FLYTO_CORE_UPDATE_DIR", str(tmp_path / "core"))
    monkeypatch.delenv("FLYTO_FLOW_MCP_TOKEN", raising=False)
    init_offline_db()
    yield
    reset_provider_hub()
    close_offline_db()


def test_hosted_provider_implementations_are_absent():
    for module_name in (
        "api.auth",
        "api.chat",
        "api.collaboration",
        "services.cloud",
        "services.collaboration",
        "services.observability.telemetry",
    ):
        assert importlib.util.find_spec(module_name) is None, module_name


def test_provider_hub_is_one_local_workspace():
    from gateway.local_context import LOCAL_WORKSPACE
    from gateway.providers.hub import get_provider_hub

    hub = get_provider_hub()
    assert hub.is_offline is True
    assert hub.is_local is False
    assert LOCAL_WORKSPACE.id == "local-workspace"
    assert "auth" not in hub.get_provider_info()


def test_application_exposes_only_local_route_families():
    from main_offline import app

    paths = set(app.openapi()["paths"])
    assert "/api/health" in paths
    assert "/api/app/version" in paths
    assert "/api/runtime-config" in paths
    assert any(path.startswith("/api/workflows") for path in paths)
    assert any(path.startswith("/api/templates") for path in paths)
    assert any(path.startswith("/api/mcp") for path in paths)

    forbidden = (
        "/api/admin",
        "/api/auth",
        "/api/billing",
        "/api/chat",
        "/api/collaboration",
        "/api/marketplace",
        "/api/messages",
        "/api/payments",
        "/api/subscriptions",
        "/api/telemetry",
        "/api/users",
        "/api/wallet",
    )
    assert not [path for path in paths if path.startswith(forbidden)]


@pytest.mark.asyncio
async def test_runtime_is_accountless_and_offline():
    from main_offline import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        runtime = (await client.get("/api/runtime-config")).json()
        capabilities = (await client.get("/api/capabilities")).json()

    assert runtime["deploymentMode"] == "local_offline"
    assert runtime["accountRequired"] is False
    assert runtime["network"]["implicitOutboundAllowed"] is False
    assert capabilities["accountRequired"] is False
    assert capabilities["network"]["runtimeDependencyDownloadAllowed"] is False


@pytest.mark.asyncio
async def test_template_crud_needs_no_identity_or_headers():
    from main_offline import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/templates/",
            json={"name": "Local workflow", "description": "SQLite", "steps": []},
        )
        assert created.status_code == 200, created.text
        template_id = created.json()["template"]["id"]

        listed = await client.get("/api/templates/")
        assert listed.status_code == 200, listed.text
        assert template_id in {item["id"] for item in listed.json()["items"]}

        updated = await client.put(
            f"/api/templates/{template_id}",
            json={"name": "Updated local workflow"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["template"]["name"] == "Updated local workflow"

        assert (await client.delete(f"/api/templates/{template_id}")).status_code == 200
        assert (await client.get(f"/api/templates/{template_id}")).status_code == 404


def test_docker_image_bundles_complete_runtime():
    body = (ROOT / "install/Dockerfile.ce").read_text(encoding="utf-8").lower()
    assert "--require-hashes" in body
    assert "flyto-core" in (BACKEND / "requirements-ce.lock").read_text(encoding="utf-8").lower()
    assert '"playwright==1.57.0"' in body
    assert "playwright install --with-deps chromium" in body
    assert "playwright_browsers_path=/opt/ms-playwright" in body
    assert "flyto_require_bundled_runtime=1" in body
    assert "headless=1" in body
    assert "check-bundled-browser.py" in body


def _write_test_wheel(path: Path, package_name: str = "flyto-core") -> str:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("core/__init__.py", "VERSION = '9.9.9'\n")
        archive.writestr(
            "flyto_core-9.9.9.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: {package_name}\nVersion: 9.9.9\n",
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_offline_core_wheel_is_verified_and_activated(tmp_path):
    from local.core_wheel import install_core_wheel, read_active_core

    wheel = tmp_path / "flyto_core-9.9.9-py3-none-any.whl"
    digest = _write_test_wheel(wheel)
    installed = install_core_wheel(wheel, digest)

    assert installed.version == "9.9.9"
    assert installed.sha256 == digest
    assert (installed.path / "core/__init__.py").is_file()
    assert read_active_core() == installed


def test_purity_gate_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-ce-purity.py"), str(ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
