from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def isolated_databases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from gateway.providers.hub import reset_provider_hub
    from gateway.storage.database import close_db, init_db
    from gateway.storage.offline_db import close_offline_db, init_offline_db

    close_db()
    close_offline_db()
    reset_provider_hub()
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("FLYTO_EXECUTION_DB_PATH", str(tmp_path / "executions.db"))
    monkeypatch.setenv("FLYTO_OFFLINE_DB_PATH", str(tmp_path / "offline.db"))
    monkeypatch.setenv("FLYTO_KEY_SALT", "test-salt-value-1234")
    monkeypatch.setenv("FLYTO_ENCRYPTION_KEY", "test-key-value-that-is-long-enough-123456")
    init_db()
    init_offline_db()
    yield
    reset_provider_hub()
    close_db()
    close_offline_db()


def test_version_contract_has_one_authoritative_semver():
    from config.version import APP_VERSION
    from scripts.check_version import check

    assert APP_VERSION == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert check(ROOT) == []


@pytest.mark.asyncio
async def test_sqlite_queue_implements_idempotency_contract():
    from gateway.storage.database import DatabaseManager
    from gateway.storage.sqlite_queue import SQLiteQueue

    DatabaseManager.execute(
        """
        INSERT INTO executions (id, workflow_id, workspace_id, started_at)
        VALUES (?, ?, ?, ?)
        """,
        ("execution-1", "workflow-1", "local-workspace", "2026-01-01T00:00:00+00:00"),
    )
    queue = SQLiteQueue()
    first = await queue.enqueue(
        "execution-1",
        "workflow-1",
        "local-workspace",
        idempotency_key="stable-operation",
        metadata={"source": "test"},
    )
    second = await queue.enqueue(
        "execution-1",
        "workflow-1",
        "local-workspace",
        idempotency_key="stable-operation",
    )

    assert first.id == second.id
    assert first.metadata == {"source": "test"}
    assert (await queue.get_by_idempotency_key("stable-operation")).id == first.id


def test_schema_migrations_are_recorded():
    from gateway.storage.database import EXECUTION_SCHEMA_VERSION, get_db
    from gateway.storage.migrations import current_schema_version
    from gateway.storage.offline_db import OFFLINE_SCHEMA_VERSION, get_offline_db

    assert current_schema_version(get_db(), "execution") == EXECUTION_SCHEMA_VERSION
    assert current_schema_version(get_offline_db(), "offline") == OFFLINE_SCHEMA_VERSION


@pytest.mark.asyncio
async def test_rbac_is_workspace_scoped_and_fails_closed():
    from gateway.providers.access.rbac import AccessRequest, RBACAccessProvider
    from gateway.providers.identity.contracts import PrincipalContext

    actor = PrincipalContext(
        id="principal-1",
        organization_id="org-1",
        workspace_ids=("workspace-1",),
        roles=("editor",),
    )
    provider = RBACAccessProvider()

    assert provider.authorize(
        actor,
        AccessRequest("workflow.update", "org-1", "workspace-1"),
    )
    assert not provider.authorize(
        actor,
        AccessRequest("audit.export", "org-1", "workspace-1"),
    )
    assert not provider.authorize(
        actor,
        AccessRequest("workflow.read", "org-2", "workspace-1"),
    )
    assert not provider.authorize(
        actor,
        AccessRequest("workflow.read", "org-1", "workspace-2"),
    )


@pytest.mark.asyncio
async def test_connection_profile_store_uses_revisions_and_local_policy():
    from services.connections import (
        ConnectionDefinition,
        ConnectionProfile,
        ConnectionScope,
        PolicyContext,
        create_local_connection_runtime,
    )

    definition = ConnectionDefinition(
        id="source.github",
        schema_version=1,
        secret_slots=("token",),
        transport_kinds=("https",),
    )
    runtime = create_local_connection_runtime((definition,))
    profile = ConnectionProfile(
        id="github-release",
        name="GitHub release",
        type="source.github",
        schema_version=1,
        scope=ConnectionScope(kind="workspace", id="local-workspace"),
        config={"baseUrl": "https://api.github.com"},
        secret_refs={
            "token": {
                "type": "secretRef",
                "credential_name": "github-token",
                "scope": "workspace",
                "scope_id": "local-workspace",
            }
        },
    )
    created = await runtime.profiles.put(profile, expected_revision=0)
    updated = await runtime.profiles.put(
        created.model_copy(update={"name": "GitHub production"}),
        expected_revision=1,
    )
    decision = await runtime.policy.authorize(
        definition,
        updated,
        PolicyContext(
            actor_id="local-workspace",
            workspace_id="local-workspace",
            operation="use",
        ),
    )

    assert updated.revision == 2
    assert decision.allowed
    with pytest.raises(RuntimeError, match="revision conflict"):
        await runtime.profiles.put(updated, expected_revision=1)


@pytest.mark.asyncio
async def test_local_audit_chain_redacts_secrets_and_exports():
    from gateway.providers.audit.local import LocalAuditProvider

    provider = LocalAuditProvider()
    await provider.log(
        "connection.use",
        "local-workspace",
        details={"token": "never-export", "nested": {"password": "also-hidden"}},
    )
    await provider.log("workflow.run", "local-workspace")

    assert await provider.verify_chain()
    rows = await provider.get_recent()
    assert rows[-1]["details"]["token"] == "[REDACTED]"
    assert rows[-1]["details"]["nested"]["password"] == "[REDACTED]"
    assert '"action": "connection.use"' in await provider.export("jsonl")
    assert "event_hash" in await provider.export("csv")


def test_extension_manifest_digest_and_signature_policy(tmp_path: Path):
    from services.extensions.manifest import (
        ExtensionPolicy,
        load_extension_manifest,
    )

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "connector.json"
    artifact.write_text('{"id":"example"}\n', encoding="utf-8")
    manifest = {
        "schema": "flyto.extension.v1",
        "id": "example.connector",
        "name": "Example Connector",
        "version": "1.0.0",
        "api_version": "v1",
        "kind": "connector",
        "permissions": ["network", "secrets.read"],
        "artifacts": [
            {
                "path": "connector.json",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
        "connection_types": [],
    }
    manifest_path = bundle / "flyto-extension.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    verified = load_extension_manifest(
        manifest_path,
        policy=ExtensionPolicy.ALLOW_UNSIGNED,
    )
    assert verified.manifest.id == "example.connector"
    with pytest.raises(ValueError, match="signature required"):
        load_extension_manifest(manifest_path)


def test_extension_manifest_ed25519_signature(tmp_path: Path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from services.extensions.manifest import load_extension_manifest

    bundle = tmp_path / "signed"
    bundle.mkdir()
    artifact = bundle / "templates.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = {
        "schema": "flyto.extension.v1",
        "id": "example.templates",
        "name": "Signed Templates",
        "version": "1.0.0",
        "api_version": "v1",
        "kind": "template-pack",
        "permissions": [],
        "artifacts": [
            {
                "path": "templates.json",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
        "connection_types": [],
    }
    private_key = Ed25519PrivateKey.generate()
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["signature"] = {
        "algorithm": "ed25519",
        "key_id": "test-key",
        "value": base64.b64encode(private_key.sign(payload)).decode(),
    }
    path = bundle / "flyto-extension.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    public_key = base64.b64encode(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
    ).decode()

    assert load_extension_manifest(
        path,
        trusted_keys={"test-key": public_key},
    ).signed


def test_official_template_pack_passes_supply_chain_and_semantic_validation():
    from services.extensions.manifest import ExtensionPolicy, load_extension_manifest
    from services.extensions.templates import load_template_packs

    extension = load_extension_manifest(
        ROOT / "extensions/official-starters/flyto-extension.json",
        policy=ExtensionPolicy.ALLOW_UNSIGNED,
    )
    templates = load_template_packs((extension,))

    assert [template.id for template in templates] == [
        "flyto2.http-get-mcp",
        "flyto2.browser-screenshot-mcp",
        "flyto2.json-to-csv-mcp",
    ]
    assert all(template.steps for template in templates)


def test_template_pack_rejects_noncontiguous_step_order(tmp_path: Path):
    from services.extensions.manifest import ExtensionPolicy, load_extension_manifest
    from services.extensions.templates import load_template_packs

    bundle = tmp_path / "invalid-template-pack"
    bundle.mkdir()
    artifact = bundle / "templates.json"
    artifact.write_text(
        json.dumps(
            {
                "schema": "flyto.template-pack.v1",
                "templates": [
                    {
                        "id": "example.invalid-template",
                        "name": "Invalid Template",
                        "steps": [
                            {
                                "id": "trigger",
                                "module": "flow.trigger",
                                "label": "Trigger",
                                "order_index": 2,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest = {
        "schema": "flyto.extension.v1",
        "id": "example.invalid-templates",
        "name": "Invalid Templates",
        "version": "1.0.0",
        "api_version": "v1",
        "kind": "template-pack",
        "permissions": [],
        "artifacts": [
            {
                "path": "templates.json",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
        "connection_types": [],
    }
    manifest_path = bundle / "flyto-extension.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    extension = load_extension_manifest(
        manifest_path,
        policy=ExtensionPolicy.ALLOW_UNSIGNED,
    )

    with pytest.raises(ValueError, match="contiguous"):
        load_template_packs((extension,))


def test_connection_catalog_and_scope_policy_contract():
    from services.connections.builtin import BUILTIN_CONNECTIONS
    from services.connections.contracts import ConnectionProfile, ConnectionScope
    from services.connections.runtime import validate_connection_profile

    definitions = {definition.id: definition for definition in BUILTIN_CONNECTIONS}
    assert {
        "source.github",
        "source.gitlab",
        "storage.s3",
        "mcp.streamable-http",
    } <= set(definitions)

    profile = ConnectionProfile(
        id="github-release",
        name="GitHub release",
        type="source.github",
        schema_version=1,
        scope=ConnectionScope(kind="project", id="project-1"),
        config={"owner": "flytohub", "repository": "flyto-flow"},
        secret_refs={
            "access_token": {
                "type": "secretRef",
                "credential_name": "github-token",
                "scope": "project",
                "scope_id": "project-1",
            }
        },
        policy={
            "allowed_hosts": ["api.github.com"],
            "allowed_ports": [443],
            "allowed_protocols": ["https"],
            "allowed_transport_kinds": ["https"],
            "allow_private_networks": False,
        },
    )
    validate_connection_profile(profile, definitions)

    cross_scope = profile.model_copy(
        update={
            "secret_refs": {
                "access_token": {
                    "type": "secretRef",
                    "credential_name": "github-token",
                    "scope": "workspace",
                    "scope_id": "workspace-1",
                }
            }
        }
    )
    with pytest.raises(ValueError, match="project boundary"):
        validate_connection_profile(cross_scope, definitions)


@pytest.mark.asyncio
async def test_runtime_capabilities_report_actual_provider_boundaries(
    monkeypatch: pytest.MonkeyPatch,
):
    from api.runtime_config import runtime_config
    from services.connections.runtime import reset_connection_runtime

    monkeypatch.delenv("FLYTO_CONNECTION_RUNTIME_FACTORY", raising=False)
    monkeypatch.delenv("FLYTO_TRACE_EXPORTER_FACTORY", raising=False)
    monkeypatch.setenv("QUEUE_BACKEND", "sqlite")
    monkeypatch.setenv("FLYTO_KEY_BACKEND", "local")
    reset_connection_runtime()

    config = await runtime_config()

    assert len(config["capabilities"]["connections"]["types"]) >= 9
    assert not config["capabilities"]["connections"]["runtimeInjection"]
    assert config["capabilities"]["connections"]["transportProvider"] == "none"
    assert config["capabilities"]["secretManagement"]["backend"] == "local"
    assert not config["capabilities"]["enterpriseProviders"]["sharedQueue"]
    assert config["capabilities"]["observability"]["localTraces"]


def test_custom_key_backend_is_allowlisted_and_validated(
    monkeypatch: pytest.MonkeyPatch,
):
    from services.credentials.backends import KeyManagementBackend
    from services.credentials.encryption import EncryptionKey

    class CustomKeyBackend(KeyManagementBackend):
        def validate_configuration(self) -> None:
            return None

        def get_key(self, version: int) -> bytes:
            return f"custom-key-{version}".encode()

        def get_current_version(self) -> int:
            return 1

        def rotate_key(self) -> int:
            return 2

        def encrypt(self, plaintext: bytes) -> bytes:
            return b"custom:" + plaintext

        def decrypt(self, ciphertext: bytes) -> bytes:
            return ciphertext.removeprefix(b"custom:")

    module = types.ModuleType("test_enterprise_provider")
    module.create_key_backend = CustomKeyBackend
    monkeypatch.setitem(sys.modules, "test_enterprise_provider", module)
    monkeypatch.setenv("FLYTO_KEY_BACKEND", "custom")
    monkeypatch.setenv(
        "FLYTO_KEY_BACKEND_FACTORY",
        "test_enterprise_provider:create_key_backend",
    )
    monkeypatch.setenv("FLYTO_PROVIDER_MODULE_ALLOWLIST", "test_enterprise_provider")
    EncryptionKey.reset()

    EncryptionKey.initialize()
    encrypted = EncryptionKey.encrypt(b"secret")
    assert encrypted == b"custom:secret"
    assert EncryptionKey.decrypt(encrypted) == b"secret"
    EncryptionKey.reset()


def test_backup_verify_and_restore_round_trip(tmp_path: Path):
    from gateway.storage.database import close_db
    from gateway.storage.offline_db import close_offline_db
    from services.operations.backup import create_backup, restore_backup, verify_backup

    source = tmp_path / "source"
    source.mkdir()
    for name, env_name in (
        ("offline.db", "FLYTO_OFFLINE_DB_PATH"),
        ("executions.db", "FLYTO_EXECUTION_DB_PATH"),
    ):
        configured = Path(os.environ[env_name])
        configured.replace(source / name)
    close_db()
    close_offline_db()

    archive = tmp_path / "backup.tar.gz"
    manifest = create_backup(source, archive)
    assert len(manifest.files) == 2
    assert verify_backup(archive).schema_name == "flyto.flow-backup.v1"

    restored = tmp_path / "restored"
    restore_backup(archive, restored)
    assert (restored / "offline.db").is_file()
    assert (restored / "executions.db").is_file()


def test_alert_webhook_rejects_insecure_urls():
    from services.observability.alerts.notifier import WebhookNotifier

    with pytest.raises(ValueError, match="HTTPS"):
        WebhookNotifier("http://alerts.example.test/hook")
