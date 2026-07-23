import asyncio
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
    assert not {
        "/api/workflows/",
        "/api/workflows/{workflow_id}",
        "/api/workflows/{workflow_id}/execute",
        "/api/workflows/{workflow_id}/history",
    } & paths


def test_mcp_tools_include_portable_audit_metadata(monkeypatch):
    import mcp_server

    monkeypatch.setattr(mcp_server, "_tool_cache", [])
    monkeypatch.setattr(mcp_server, "_workflow_map", {})
    monkeypatch.setattr(
        mcp_server,
        "_api_request",
        lambda *_args, **_kwargs: {
            "items": [{
                "id": "wf-audit",
                "name": "Audit project",
                "steps": [{
                    "module": "flow.trigger",
                    "params": {
                        "trigger_type": "mcp",
                        "tool_name": "audit_project",
                        "risk_level": "review",
                        "approval_policy": "operator",
                        "evidence_refs": ["execution"],
                    },
                }],
            }]
        },
    )

    tool = mcp_server._refresh_tools(force=True)[0]

    assert tool["_meta"]["flyto2/source"] == {
        "type": "workflow", "id": "wf-audit", "name": "Audit project"
    }
    assert tool["_meta"]["flyto2/contractVersion"] == "flyto.mcp.workflow-tool.v1"
    assert len(tool["_meta"]["flyto2/fingerprint"]) == 64
    assert tool["_meta"]["flyto2/riskLevel"] == "review"
    assert tool["_meta"]["flyto2/approvalPolicy"] == "operator"
    assert tool["_meta"]["flyto2/evidenceRefs"] == ["execution"]


def test_mcp_origin_guard_allows_loopback_development_ports():
    from api.mcp import _assert_origin_allowed

    _assert_origin_allowed("http://127.0.0.1:3000", "127.0.0.1:9000")
    with pytest.raises(Exception) as error:
        _assert_origin_allowed("https://evil.example", "127.0.0.1:9000")
    assert getattr(error.value, "status_code", None) == 403


def test_mcp_loopback_proxy_trust_is_explicit_and_host_bound(monkeypatch):
    from types import SimpleNamespace

    from api.mcp import _request_is_loopback

    bridge_request = SimpleNamespace(client=SimpleNamespace(host="172.17.0.1"))
    external_request = SimpleNamespace(client=SimpleNamespace(host="8.8.8.8"))

    monkeypatch.delenv("FLYTO_FLOW_MCP_TRUST_LOOPBACK_PROXY", raising=False)
    assert not _request_is_loopback(bridge_request, "127.0.0.1:9000")

    monkeypatch.setenv("FLYTO_FLOW_MCP_TRUST_LOOPBACK_PROXY", "1")
    assert _request_is_loopback(bridge_request, "127.0.0.1:9000")
    assert not _request_is_loopback(bridge_request, "flow.example:9000")
    assert not _request_is_loopback(external_request, "127.0.0.1:9000")


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


async def _run_and_wait(client: httpx.AsyncClient, workflow_yaml: str, params: dict) -> dict:
    """Start a workflow via /api/workflows/run and poll until it settles.

    Exercises the real execution path end-to-end (not just module wiring in
    isolation) — this is how the manual verification during development caught
    bugs that unit tests on individual functions missed.
    """
    started = await client.post(
        "/api/workflows/run",
        json={"workflow_yaml": workflow_yaml, "params": params},
    )
    assert started.status_code == 200, started.text
    execution_id = started.json()["execution_id"]

    for _ in range(50):
        status = await client.get(f"/api/executions/{execution_id}")
        assert status.status_code == 200, status.text
        execution = status.json()["execution"]
        if execution["status"] in ("completed", "failed"):
            return execution
        await asyncio.sleep(0.1)

    raise AssertionError(f"Execution {execution_id} did not settle in time")


@pytest.mark.asyncio
async def test_workflow_run_actually_executes_branch_node():
    from main_offline import app

    workflow_yaml = (
        "name: Branch Test\n"
        "steps:\n"
        "  - id: branch\n"
        "    module: flow.branch\n"
        "    label: Branch\n"
        "    params:\n"
        "      condition: \"${count} > 5\"\n"
        "    order_index: 0\n"
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        execution = await _run_and_wait(client, workflow_yaml, {"count": 10})

    assert execution["status"] == "completed"
    branch_output = execution["node_outputs"]["branch"]
    assert branch_output["__event__"] == "true"
    assert branch_output["result"] is True


@pytest.mark.asyncio
async def test_workflow_run_actually_executes_loop_node():
    from main_offline import app

    workflow_yaml = (
        "name: Loop Test\n"
        "steps:\n"
        "  - id: loop\n"
        "    module: flow.loop\n"
        "    label: Loop\n"
        "    params:\n"
        "      times: 3\n"
        "      index_var: idx\n"
        "    order_index: 0\n"
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        execution = await _run_and_wait(client, workflow_yaml, {})

    assert execution["status"] == "completed"
    loop_output = execution["node_outputs"]["loop"]
    assert loop_output["outputs"]["iterate"]["total"] == 3


@pytest.mark.asyncio
async def test_workflow_run_actually_copies_a_file():
    """file.copy confines paths to the app's own working directory (rejects
    anything that resolves outside it), so the fixtures must live there too —
    not under pytest's tmp_path, which is deliberately out of bounds."""
    from main_offline import app

    source = Path("ce_release_test_source.txt")
    destination = Path("ce_release_test_dest.txt")
    source.write_text("hello file test", encoding="utf-8")
    try:
        workflow_yaml = (
            "name: File Copy Test\n"
            "steps:\n"
            "  - id: copy\n"
            "    module: file.copy\n"
            "    label: Copy File\n"
            "    params:\n"
            f"      source: {source.name}\n"
            f"      destination: {destination.name}\n"
            "      overwrite: true\n"
            "    order_index: 0\n"
        )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            execution = await _run_and_wait(client, workflow_yaml, {})

        assert execution["status"] == "completed", execution.get("error")
        assert destination.read_text(encoding="utf-8") == "hello file test"
    finally:
        source.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_nested_execution_modules_are_denied_by_default():
    """flow.invoke / flow.subflow are real "run arbitrary nested workflow"
    gadgets in flyto-core, but flyto-core's stub flow.subflow implementation
    never actually executes anything it's pointed at — so this module must
    stay behind the capability denylist by default, not just be inert."""
    from main_offline import app

    workflow_yaml = (
        "name: Subflow Test\n"
        "steps:\n"
        "  - id: sub\n"
        "    module: flow.subflow\n"
        "    label: Subflow\n"
        "    params:\n"
        "      workflow_ref: this/does/not/exist.yaml\n"
        "      execution_mode: inline\n"
        "      input_mapping: {}\n"
        "    order_index: 0\n"
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        execution = await _run_and_wait(client, workflow_yaml, {})

    assert execution["status"] == "failed"
    assert "capability policy" in execution["error"]


@pytest.mark.asyncio
async def test_template_update_can_explicitly_clear_a_field():
    from main_offline import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        fallback = await client.post(
            "/api/templates/",
            json={"name": "Fallback", "steps": []},
        )
        source = await client.post(
            "/api/templates/",
            json={
                "name": "Source",
                "steps": [],
                "error_workflow_id": fallback.json()["template"]["id"],
            },
        )
        template_id = source.json()["template"]["id"]
        assert source.json()["template"]["error_workflow_id"] is not None

        # Explicitly clearing a field to null must not be treated as "no fields
        # to update" (it was, before model_fields_set replaced `is not None`).
        cleared = await client.put(
            f"/api/templates/{template_id}",
            json={"error_workflow_id": None},
        )
        assert cleared.status_code == 200, cleared.text
        assert cleared.json()["template"]["error_workflow_id"] is None

        # A request with no fields at all is still rejected.
        empty = await client.put(f"/api/templates/{template_id}", json={})
        assert empty.status_code == 400


@pytest.mark.asyncio
async def test_first_run_starter_template_seed_is_idempotent():
    from gateway.local_context import LOCAL_WORKSPACE
    from gateway.providers.hub import get_data_provider
    from local.lifespan_local import seed_starter_templates

    await seed_starter_templates()
    await seed_starter_templates()

    templates = await get_data_provider().templates.list_workspace_templates(
        workspace_id=LOCAL_WORKSPACE.id,
        page=1,
        page_size=20,
    )
    assert templates.total == 2
    starters = {template.name: template for template in templates.items}
    assert set(starters) == {"HTTP GET Request Tool", "Browser Screenshot Tool"}

    http_starter = starters["HTTP GET Request Tool"]
    assert http_starter.steps[0]["module"] == "flow.trigger"
    assert http_starter.steps[0]["params"]["trigger_type"] == "mcp"
    assert http_starter.steps[1]["module"] == "core.api.http_get"

    browser_starter = starters["Browser Screenshot Tool"]
    assert browser_starter.steps[0]["module"] == "flow.trigger"
    assert browser_starter.steps[0]["params"]["trigger_type"] == "mcp"
    assert [step["module"] for step in browser_starter.steps[1:]] == [
        "browser.ensure",
        "browser.goto",
        "browser.screenshot",
        "browser.close",
    ]


@pytest.mark.asyncio
async def test_error_workflow_resolution_uses_saved_templates():
    import yaml

    from gateway.local_context import LOCAL_WORKSPACE
    from gateway.providers.data.models import TemplateCreateDTO
    from gateway.providers.hub import get_data_provider
    from services.runtime.execution.error_handler import get_error_workflow_id
    from services.runtime.execution.template_loader import fetch_workflow_yaml

    templates = get_data_provider().templates
    fallback = await templates.create_template(
        workspace_id=LOCAL_WORKSPACE.id,
        data=TemplateCreateDTO(
            name="Failure handler",
            steps=[{"id": "notify", "module": "core.api.http_post", "params": {}}],
        ),
    )
    source = await templates.create_template(
        workspace_id=LOCAL_WORKSPACE.id,
        data=TemplateCreateDTO(
            name="Primary workflow",
            steps=[],
            error_workflow_id=fallback.id,
        ),
    )

    assert (
        await get_error_workflow_id(source.id, LOCAL_WORKSPACE.id)
        == fallback.id
    )
    fallback_yaml = await fetch_workflow_yaml(fallback.id, LOCAL_WORKSPACE.id)
    parsed = yaml.safe_load(fallback_yaml)
    assert parsed["name"] == "Failure handler"
    assert parsed["steps"][0]["module"] == "core.api.http_post"


@pytest.mark.asyncio
async def test_alert_scheduler_reads_current_collector_samples(monkeypatch):
    from types import SimpleNamespace

    from services.observability.alerts import scheduler as scheduler_module

    collector = SimpleNamespace(
        get_all_metrics=lambda: [
            SimpleNamespace(
                name="requests_total",
                samples=[SimpleNamespace(value=7.0)],
            )
        ]
    )
    monkeypatch.setattr(scheduler_module, "get_collector", lambda: collector)

    metrics = await scheduler_module.AlertScheduler(
        manager=SimpleNamespace()
    )._collect_metrics()

    assert metrics["requests_total"] == 7.0


def test_docker_image_bundles_complete_runtime():
    body = (ROOT / "install/Dockerfile.ce").read_text(encoding="utf-8").lower()
    env_example = (ROOT / "install/.env.ce.example").read_text(encoding="utf-8")
    assert "--require-hashes" in body
    assert "flyto-core" in (BACKEND / "requirements-ce.lock").read_text(encoding="utf-8").lower()
    assert '"playwright==1.57.0"' in body
    assert "playwright install --with-deps chromium" in body
    assert "playwright_browsers_path=/opt/ms-playwright" in body
    assert "flyto_require_bundled_runtime=1" in body
    assert "headless=1" in body
    assert "check-bundled-browser.py" in body
    assert "FLYTO_OFFLINE_DB_PATH=/data/flyto/offline.db" in env_example
    assert "FLYTO_EXECUTION_DB_PATH=/data/flyto/executions.db" in env_example
    assert "chown -r appuser:appuser /data /app /home/appuser" in body


def test_dark_mode_scoped_selectors_use_descendant_global_form():
    sources = (
        "src/ui/web/frontend/src/components/common/LoadingButton.vue",
        "src/ui/web/frontend/src/components/common/ToggleSwitch.vue",
        "src/ui/web/frontend/src/components/templates/TemplateCard.vue",
        "src/ui/web/frontend/src/components/templates/TemplateListItem.vue",
    )

    for source in sources:
        body = (ROOT / source).read_text(encoding="utf-8")
        assert ":global(.dark) " not in body, source


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


def test_license_policy_gate_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_license_policy.py"), str(ROOT)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.asyncio
async def test_cron_errors_do_not_expose_exception_text(monkeypatch):
    from api.triggers.local_routes import get_cron_next_run, validate_cron_expression
    from api.triggers.models import CronValidateRequest
    from services.infra.scheduler import CronParser

    def fail(*_args, **_kwargs):
        raise RuntimeError("secret-internal-error")

    monkeypatch.setattr(CronParser, "get_next_run", fail)
    validation = await validate_cron_expression(CronValidateRequest(expression="* * * * *"))
    assert validation["error"] == "Invalid cron expression"
    assert "secret-internal-error" not in str(validation)

    with pytest.raises(Exception) as error:
        await get_cron_next_run("* * * * *")
    assert getattr(error.value, "detail", None) == "Invalid cron expression"
    assert "secret-internal-error" not in str(getattr(error.value, "detail", ""))
