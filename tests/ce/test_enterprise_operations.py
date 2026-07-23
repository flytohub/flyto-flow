from __future__ import annotations

import asyncio
import hashlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from gateway.storage.database import close_db, init_db
    from gateway.storage.offline_db import close_offline_db, init_offline_db
    from gateway.storage.queue_factory import reset_queue
    from services.connections.runtime import reset_connection_runtime
    from services.credentials.encryption import EncryptionKey

    close_db()
    close_offline_db()
    reset_queue()
    reset_connection_runtime()
    EncryptionKey.reset()
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("FLYTO_EXECUTION_DB_PATH", str(tmp_path / "executions.db"))
    monkeypatch.setenv("FLYTO_OFFLINE_DB_PATH", str(tmp_path / "offline.db"))
    monkeypatch.setenv("FLYTO_KEY_SALT", "test-salt-value-1234")
    monkeypatch.setenv(
        "FLYTO_ENCRYPTION_KEY",
        "test-key-value-that-is-long-enough-123456",
    )
    monkeypatch.setenv("FLYTO_KEY_BACKEND", "local")
    init_db()
    init_offline_db()
    yield
    EncryptionKey.reset()
    reset_connection_runtime()
    reset_queue()
    close_db()
    close_offline_db()


@pytest.mark.asyncio
async def test_queue_load_claims_each_job_once_and_recovers_expired_lease():
    from gateway.storage.database import transaction
    from gateway.storage.sqlite_queue import SQLiteQueue

    job_count = 150
    with transaction(immediate=True) as connection:
        connection.executemany(
            """
            INSERT INTO executions (id, workflow_id, workspace_id, started_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    f"execution-{index}",
                    "workflow-load",
                    "local-workspace",
                    "2026-01-01T00:00:00+00:00",
                )
                for index in range(job_count)
            ],
        )
    queue = SQLiteQueue()
    await asyncio.gather(
        *(
            queue.enqueue(
                f"execution-{index}",
                "workflow-load",
                "local-workspace",
                idempotency_key=f"operation-{index}",
            )
            for index in range(job_count)
        )
    )

    abandoned = await queue.dequeue("worker-abandoned", lease_duration_seconds=-1)
    assert abandoned is not None
    recovered = await queue.dequeue("worker-recovery", lease_duration_seconds=30)
    assert recovered is not None
    assert recovered.id == abandoned.id
    assert recovered.attempts == 2
    assert not await queue.ack(recovered.id, "worker-abandoned")
    assert await queue.ack(recovered.id, "worker-recovery")

    claimed_ids = {recovered.id}

    async def drain(worker_id: str) -> None:
        while job := await queue.dequeue(worker_id, lease_duration_seconds=30):
            assert job.id not in claimed_ids
            claimed_ids.add(job.id)
            assert await queue.ack(job.id, worker_id)

    await asyncio.gather(*(drain(f"worker-{index}") for index in range(8)))
    stats = await queue.get_stats()
    assert len(claimed_ids) == job_count
    assert stats.completed == job_count
    assert stats.pending == stats.running == stats.failed == 0


def test_migration_failure_rolls_back_schema_and_ledger():
    from gateway.storage.migrations import Migration, apply_migrations

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    def fail_after_write(database: sqlite3.Connection) -> None:
        database.execute("CREATE TABLE partial_change (id TEXT)")
        raise RuntimeError("stop")

    migration = Migration(1, "rollback-check", "rollback-check:v1", fail_after_write)
    with pytest.raises(RuntimeError, match="stop"):
        apply_migrations(connection, "test", (migration,))

    assert connection.execute(
        "SELECT name FROM sqlite_master WHERE name = 'partial_change'"
    ).fetchone() is None
    assert connection.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE namespace = 'test'"
    ).fetchone()[0] == 0


def test_migrations_reject_version_gaps_and_unknown_future_history():
    from gateway.storage.migrations import Migration, apply_migrations

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    with pytest.raises(RuntimeError, match="contiguous"):
        apply_migrations(
            connection,
            "test",
            (Migration(2, "gap", "gap:v1", lambda _database: None),),
        )

    migration = Migration(1, "baseline", "baseline:v1", lambda _database: None)
    apply_migrations(connection, "test", (migration,))
    connection.execute(
        """
        INSERT INTO schema_migrations
            (namespace, version, name, checksum, applied_at)
        VALUES ('test', 2, 'future', 'future', '2026-01-01T00:00:00+00:00')
        """
    )
    connection.commit()
    with pytest.raises(RuntimeError, match="unsupported test migration"):
        apply_migrations(connection, "test", (migration,))


def test_extension_runtime_rejects_unsigned_and_unmanaged_bundles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from services.extensions.runtime import verify_configured_extensions

    root = tmp_path / "extensions"
    unmanaged = root / "unmanaged"
    unmanaged.mkdir(parents=True)
    (unmanaged / "plugin.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("FLYTO_EXTENSIONS_DIR", str(root))
    monkeypatch.setenv("FLYTO_PLUGINS_DIR", str(root))
    with pytest.raises(ValueError, match="missing flyto-extension"):
        verify_configured_extensions()

    for child in unmanaged.iterdir():
        child.unlink()
    unmanaged.rmdir()
    bundle = root / "network-plugin"
    bundle.mkdir()
    artifact = bundle / "plugin.json"
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = {
        "schema": "flyto.extension.v1",
        "id": "example.network-plugin",
        "name": "Network Plugin",
        "version": "1.0.0",
        "api_version": "v1",
        "kind": "plugin",
        "permissions": ["network"],
        "artifacts": [
            {
                "path": "plugin.json",
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
    }
    (bundle / "flyto-extension.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    monkeypatch.setenv("FLYTO_EXTENSION_SIGNATURE_POLICY", "allow-unsigned")
    with pytest.raises(PermissionError, match="ungranted"):
        verify_configured_extensions()
    monkeypatch.setenv(
        "FLYTO_EXTENSION_PERMISSION_GRANTS",
        '{"example.network-plugin":["network"]}',
    )
    assert len(verify_configured_extensions()) == 1
    (bundle / "undeclared.txt").write_text("not signed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="undeclared files"):
        verify_configured_extensions()


def test_extension_signing_cli_refreshes_digest_and_produces_valid_signature(
    tmp_path: Path,
):
    from services.extensions.manifest import (
        ExtensionPolicy,
        load_extension_manifest,
    )

    bundle = tmp_path / "signed-extension"
    bundle.mkdir()
    artifact = bundle / "connector.json"
    artifact.write_text('{"name":"signed"}\n', encoding="utf-8")
    manifest_path = bundle / "flyto-extension.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "flyto.extension.v1",
                "id": "example.signed-connector",
                "name": "Signed Connector",
                "version": "1.0.0",
                "api_version": "v1",
                "kind": "connector",
                "permissions": [],
                "artifacts": [{"path": "connector.json", "sha256": "0" * 64}],
                "connection_types": [],
            }
        ),
        encoding="utf-8",
    )
    private_key = tmp_path / "release.pem"
    public_key = tmp_path / "release.pub"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/sign_extension.py"),
            "generate-key",
            "--private-key",
            str(private_key),
            "--public-key",
            str(public_key),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert private_key.stat().st_mode & 0o777 == 0o600
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/sign_extension.py"),
            "sign",
            str(manifest_path),
            "--private-key",
            str(private_key),
            "--key-id",
            "release-2026",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    verified = load_extension_manifest(
        manifest_path,
        policy=ExtensionPolicy.REQUIRE_SIGNATURE,
        trusted_keys={"release-2026": public_key.read_text(encoding="ascii").strip()},
    )
    assert verified.signed
    assert verified.manifest.artifacts[0].sha256 == hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()


@pytest.mark.asyncio
async def test_connection_profiles_reject_plaintext_secrets_and_enforce_policy():
    from services.connections import (
        ConnectionProfile,
        ConnectionScope,
        ConnectionService,
        PolicyContext,
        configure_connection_runtime,
    )

    runtime = configure_connection_runtime()
    profile = ConnectionProfile(
        id="production-api",
        name="Production API",
        type="http.api",
        schema_version=1,
        scope=ConnectionScope(kind="workspace", id="local-workspace"),
        config={"base_url": "https://api.example.test", "api_key": "plaintext"},
    )
    with pytest.raises(ValueError, match="secret_refs"):
        await ConnectionService.put_profile(profile, expected_revision=0)

    saved = await ConnectionService.put_profile(
        profile.model_copy(
            update={
                "config": {"base_url": "https://api.example.test"},
                "policy": {"allowed_workflow_ids": ["workflow-allowed"]},
            }
        ),
        expected_revision=0,
    )
    decision = await runtime.policy.authorize(
        runtime.catalog.get("http.api"),
        saved,
        PolicyContext(
            actor_id="local-workspace",
            workspace_id="local-workspace",
            workflow_id="workflow-denied",
            operation="use",
        ),
    )
    assert not decision.allowed
    assert decision.reason == "workflow_not_allowed"


@pytest.mark.asyncio
async def test_connection_profiles_enforce_schema_secret_and_policy_boundaries():
    from services.connections import (
        ConnectionProfile,
        ConnectionScope,
        ConnectionService,
        configure_connection_runtime,
    )

    configure_connection_runtime()
    profile = ConnectionProfile(
        id="strict-api",
        name="Strict API",
        type="http.api",
        schema_version=1,
        scope=ConnectionScope(kind="workspace", id="local-workspace"),
        config={
            "base_url": "not a URI",
            "timeout_seconds": "slow",
        },
    )
    with pytest.raises(ValueError, match=r"base_url \(format\)"):
        await ConnectionService.put_profile(profile, expected_revision=0)

    with pytest.raises(ValueError, match="crosses workspace boundary"):
        await ConnectionService.put_profile(
            profile.model_copy(
                update={
                    "config": {"base_url": "https://api.example.test"},
                    "secret_refs": {
                        "api_key": {
                            "type": "secretRef",
                            "credential_name": "api-key",
                            "scope": "workspace",
                            "scope_id": "another-workspace",
                        }
                    },
                }
            ),
            expected_revision=0,
        )

    with pytest.raises(ValueError, match="Unknown connection policy fields"):
        await ConnectionService.put_profile(
            profile.model_copy(
                update={
                    "config": {"base_url": "https://api.example.test"},
                    "policy": {"administrator": True},
                }
            ),
            expected_revision=0,
        )


def test_connection_definition_requires_strict_valid_json_schema():
    from pydantic import ValidationError
    from services.connections import ConnectionDefinition

    with pytest.raises(ValidationError, match="Draft 2020-12"):
        ConnectionDefinition(
            id="example.invalid",
            schema_version=1,
            config_schema={
                "type": "object",
                "properties": {"port": {"type": "not-a-json-schema-type"}},
                "additionalProperties": False,
            },
        )
    with pytest.raises(ValidationError, match="reject additional properties"):
        ConnectionDefinition(
            id="example.open",
            schema_version=1,
            config_schema={"type": "object", "properties": {}},
        )


@pytest.mark.asyncio
async def test_connection_api_exposes_catalog_and_revisioned_profiles():
    import httpx
    from fastapi import FastAPI

    from api.connections import router
    from services.connections import configure_connection_runtime

    configure_connection_runtime()
    app = FastAPI()
    app.include_router(router, prefix="/api")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        catalog = await client.get("/api/connections/catalog")
        assert catalog.status_code == 200
        assert "http.api" in {
            item["id"] for item in catalog.json()["connection_types"]
        }
        created = await client.put(
            "/api/connections/profiles/example-api",
            json={
                "name": "Example API",
                "type": "http.api",
                "schema_version": 1,
                "config": {"base_url": "https://api.example.test"},
                "expected_revision": 0,
            },
        )
        assert created.status_code == 200
        assert created.json()["profile"]["revision"] == 1
        conflict = await client.put(
            "/api/connections/profiles/example-api",
            json={
                "name": "Example API",
                "type": "http.api",
                "schema_version": 1,
                "config": {"base_url": "https://api.example.test"},
                "expected_revision": 0,
            },
        )
        assert conflict.status_code == 409
        listed = await client.get("/api/connections/profiles")
        assert len(listed.json()["profiles"]) == 1


def test_secret_variables_use_key_backend_and_browser_resolution_excludes_them():
    from gateway.storage.database import DatabaseManager
    from gateway.storage.variable_repo import (
        Environment,
        Variable,
        VariableRepository,
        VariableScope,
    )

    VariableRepository.create(
        Variable(
            id="",
            name="API_TOKEN",
            value="never-store-plaintext",
            scope=VariableScope.WORKFLOW,
            scope_id="workflow-1",
            environment=Environment.DEVELOPMENT,
            is_secret=True,
        )
    )
    row = DatabaseManager.fetchone(
        "SELECT value, encrypted_value FROM variables WHERE name = ?",
        ("API_TOKEN",),
    )
    assert row["value"] == ""
    assert row["encrypted_value"].startswith("enc:v1:")
    assert "never-store-plaintext" not in row["encrypted_value"]
    assert VariableRepository.resolve_variables("workflow-1") == {
        "API_TOKEN": "never-store-plaintext"
    }
    assert VariableRepository.resolve_variables(
        "workflow-1",
        include_secrets=False,
    ) == {}


def test_kms_envelope_binds_encryption_context(monkeypatch: pytest.MonkeyPatch):
    from services.credentials.backends.aws_kms import (
        AWSKMSBackend,
        ENCRYPTION_CONTEXT,
        ENVELOPE_MAGIC,
    )

    class FakeKMS:
        def describe_key(self, **kwargs):
            assert kwargs["KeyId"] == "key-1"
            return {
                "KeyMetadata": {
                    "KeyState": "Enabled",
                    "KeyUsage": "ENCRYPT_DECRYPT",
                }
            }

        def generate_data_key(self, **kwargs):
            assert kwargs["EncryptionContext"] == ENCRYPTION_CONTEXT
            return {"Plaintext": b"k" * 32, "CiphertextBlob": b"wrapped-key"}

        def decrypt(self, **kwargs):
            if "EncryptionContext" in kwargs:
                assert kwargs["EncryptionContext"] == ENCRYPTION_CONTEXT
            assert kwargs["KeyId"] == "key-1"
            return {"Plaintext": b"k" * 32}

    backend = AWSKMSBackend.__new__(AWSKMSBackend)
    backend._client = FakeKMS()
    backend._key_id = "key-1"
    encrypted = backend.encrypt(b"credential")
    assert encrypted.startswith(ENVELOPE_MAGIC)
    assert backend.decrypt(encrypted) == b"credential"
    backend.validate_configuration()
    with pytest.raises(ValueError, match="Legacy KMS"):
        backend.decrypt(encrypted.removeprefix(ENVELOPE_MAGIC))
    monkeypatch.setenv("FLYTO_KMS_ALLOW_LEGACY_CIPHERTEXT", "true")
    assert backend.decrypt(encrypted.removeprefix(ENVELOPE_MAGIC)) == b"credential"


def test_vault_requires_tls_even_before_client_initialization():
    from services.credentials.backends.vault import VaultKeyBackend

    with pytest.raises(ValueError, match="HTTPS"):
        VaultKeyBackend(
            vault_addr="http://vault.example.test",
            vault_token="test-token",
        )


def test_vault_rejects_ciphertext_without_authenticated_envelope():
    from services.credentials.backends.vault import VaultKeyBackend

    backend = VaultKeyBackend.__new__(VaultKeyBackend)
    with pytest.raises(ValueError, match="Invalid Vault ciphertext envelope"):
        backend.decrypt(b"vault:v1:untrusted")


@pytest.mark.asyncio
async def test_audit_chain_detects_tampering_after_concurrent_appends():
    from gateway.providers.audit.local import LocalAuditProvider
    from gateway.storage.database import DatabaseManager

    provider = LocalAuditProvider()
    await asyncio.gather(
        *(
            provider.log(
                "workflow.run",
                f"actor-{index % 5}",
                resource_id=f"workflow-{index}",
            )
            for index in range(100)
        )
    )
    assert await provider.verify_chain()
    DatabaseManager.execute(
        "UPDATE audit_events SET action = 'tampered' WHERE sequence = 50"
    )
    assert not await provider.verify_chain()


def test_error_redaction_covers_nested_inputs_and_exception_tokens():
    from services.observability.structured_logging import (
        redact_error_message,
        redact_sensitive_data,
    )

    redacted = redact_sensitive_data(
        {
            "username": "operator",
            "password": "never-log-this",
            "nested": [{"api_key": "also-secret"}],
        }
    )
    assert redacted == {
        "username": "operator",
        "password": "[REDACTED]",
        "nested": [{"api_key": "[REDACTED]"}],
    }
    assert redact_error_message(
        "provider failed with sk-abcdefghijklmnopqrstuvwxyz123456"
    ) == "[REDACTED]"


def test_alert_webhook_rejects_query_secrets(monkeypatch: pytest.MonkeyPatch):
    from services.observability.alerts.notifier import WebhookNotifier

    monkeypatch.setenv("FLYTO_ALERT_WEBHOOK_ALLOWED_HOSTS", "alerts.example.test")
    with pytest.raises(ValueError, match="query parameters"):
        WebhookNotifier("https://alerts.example.test/hook?token=secret")


def test_backup_digest_tampering_is_rejected(tmp_path: Path):
    from gateway.storage.database import close_db
    from gateway.storage.offline_db import close_offline_db
    from services.operations.backup import create_backup, verify_backup

    source = tmp_path / "source"
    source.mkdir()
    close_db()
    close_offline_db()
    Path(os.environ["FLYTO_EXECUTION_DB_PATH"]).replace(source / "executions.db")
    Path(os.environ["FLYTO_OFFLINE_DB_PATH"]).replace(source / "offline.db")
    original = tmp_path / "original.tar.gz"
    create_backup(source, original)

    tampered = tmp_path / "tampered.tar.gz"
    with tarfile.open(original, "r:gz") as source_archive:
        members = {
            member.name: source_archive.extractfile(member).read()
            for member in source_archive.getmembers()
        }
    members["offline.db"] += b"tamper"
    with tarfile.open(tampered, "w:gz") as destination:
        for name, value in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(value)
            destination.addfile(info, io.BytesIO(value))

    with pytest.raises(ValueError, match="size mismatch"):
        verify_backup(tampered)


def test_restore_rolls_back_all_databases_when_replacement_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from services.operations.backup import create_backup, restore_backup

    source = tmp_path / "backup-source"
    target = tmp_path / "restore-target"
    source.mkdir()
    target.mkdir()
    for name in ("offline.db", "executions.db"):
        with sqlite3.connect(source / name) as connection:
            connection.execute("CREATE TABLE marker (value TEXT NOT NULL)")
            connection.execute("INSERT INTO marker VALUES ('new')")
        with sqlite3.connect(target / name) as connection:
            connection.execute("CREATE TABLE marker (value TEXT NOT NULL)")
            connection.execute("INSERT INTO marker VALUES ('original')")

    archive = tmp_path / "backup.tar.gz"
    create_backup(source, archive)
    original_replace = Path.replace

    def fail_second_replacement(path: Path, destination: Path):
        if path.name == "executions.db.restore":
            raise OSError("injected replacement failure")
        return original_replace(path, destination)

    monkeypatch.setattr(Path, "replace", fail_second_replacement)
    with pytest.raises(OSError, match="injected"):
        restore_backup(archive, target, allow_overwrite=True)

    monkeypatch.setattr(Path, "replace", original_replace)
    for name in ("offline.db", "executions.db"):
        with sqlite3.connect(target / name) as connection:
            assert connection.execute("SELECT value FROM marker").fetchone()[0] == "original"
        assert not (target / f"{name}.restore-previous").exists()


def test_sso_configuration_requires_protocol_metadata():
    from gateway.providers.identity.contracts import (
        SSOConfiguration,
        SSOProtocol,
    )

    with pytest.raises(ValueError, match="discovery_url"):
        SSOConfiguration(
            id="sso-1",
            organization_id="org-1",
            protocol=SSOProtocol.OIDC,
            issuer="https://id.example.test",
            client_id="client-1",
        )
    configuration = SSOConfiguration(
        id="sso-1",
        organization_id="org-1",
        protocol=SSOProtocol.OIDC,
        issuer="https://id.example.test",
        discovery_url="https://id.example.test/.well-known/openid-configuration",
        client_id="client-1",
        allowed_domains=["EXAMPLE.TEST", "example.test"],
    )
    assert configuration.allowed_domains == ["example.test"]


def test_provider_allowlist_requires_package_boundary(
    monkeypatch: pytest.MonkeyPatch,
):
    from gateway.providers.loading import (
        configured_provider_prefixes,
        is_provider_module_allowed,
        load_provider_factory,
    )

    monkeypatch.setenv("FLYTO_PROVIDER_MODULE_ALLOWLIST", "trusted.providers")
    assert configured_provider_prefixes() == ("trusted.providers",)
    assert is_provider_module_allowed("trusted.providers")
    assert is_provider_module_allowed("trusted.providers.queue")
    assert not is_provider_module_allowed("trusted.providers_evil")
    with pytest.raises(ValueError, match="public_factory"):
        load_provider_factory(
            "trusted.providers:_private",
            setting_name="TEST_PROVIDER",
        )


def test_rbac_role_bindings_isolate_organizations_and_workspaces():
    from gateway.providers.access.rbac import AccessRequest, RBACAccessProvider
    from gateway.providers.identity.contracts import PrincipalContext, RoleBinding

    provider = RBACAccessProvider()
    principal = PrincipalContext(
        id="principal-1",
        organization_id="organization-1",
        workspace_ids=("workspace-a", "workspace-b"),
        role_bindings=(
            RoleBinding(
                role="editor",
                organization_id="organization-1",
                workspace_id="workspace-a",
            ),
            RoleBinding(
                role="viewer",
                organization_id="organization-1",
                workspace_id="workspace-b",
            ),
        ),
    )
    assert provider.authorize(
        principal,
        AccessRequest("workflow.update", "organization-1", "workspace-a"),
    )
    assert not provider.authorize(
        principal,
        AccessRequest("workflow.update", "organization-1", "workspace-b"),
    )
    assert not provider.authorize(
        principal,
        AccessRequest("workflow.read", "organization-2", "workspace-a"),
    )
    assert not provider.authorize(
        principal,
        AccessRequest("organization.update", "organization-1"),
    )
