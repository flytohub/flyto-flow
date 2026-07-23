# Operations

## Data Layout

The container stores mutable state under `/data/flyto`:

- `offline.db`: workflows, templates, and connection profiles;
- `executions.db`: executions, queue jobs, credentials, metrics, traces, and
  the audit chain;
- optional operator-installed Core and extension files.

Both databases use WAL mode, foreign keys, a busy timeout, and an explicit
`schema_migrations` ledger.

Every migration has an immutable version, name, and explicit fingerprint.
Pending migrations run under `BEGIN IMMEDIATE`, and the schema change and
ledger row commit together. Changed migration history and duplicate versions
fail startup.

## Backup

Create a backup while the service is running:

```bash
python scripts/flow_ops.py backup \
  --data-dir /data/flyto \
  --output /backups/flyto-flow-2026-07-23.tar.gz
```

The command uses SQLite's online backup API. It does not copy live WAL files.
The archive contains a versioned manifest, database schema versions, file
sizes, and SHA-256 digests.

Verify a backup independently:

```bash
python scripts/flow_ops.py verify-backup \
  /backups/flyto-flow-2026-07-23.tar.gz
```

Verification checks the archive allowlist, manifest, application major
or pre-1.0 minor compatibility line, schema versions, file digests, declared
sizes, a configurable extracted-size limit, and SQLite integrity. Archives
with duplicate, undeclared, unsafe, or future-schema members are rejected
before restore.

## Restore

Stop all API and worker processes before restore:

```bash
python scripts/flow_ops.py restore \
  /backups/flyto-flow-2026-07-23.tar.gz \
  --data-dir /data/flyto
```

Restore refuses to overwrite existing databases unless `--overwrite` is
provided. All files are verified and staged before replacement. If a
replacement fails, already replaced databases are rolled back.

## Upgrade And Compatibility Policy

1. Create and verify a backup before every upgrade.
2. Test restore into a separate data directory.
3. Stop API and worker processes.
4. Deploy the new immutable image by digest.
5. Start one instance so migrations complete before scaling workers.
6. Verify `/api/health`, queue health, extension admission, and audit-chain
   integrity before restoring traffic.

Backups from a newer application or newer database schema are rejected. For
`0.x` releases, the minor version is the compatibility boundary. Starting
with `1.0.0`, the major version is the compatibility boundary. Migrations move
forward only; rollback means restoring the pre-upgrade backup and previous
image, not running destructive down migrations.

## Queue And Workers

Single-instance deployments use SQLite:

```text
QUEUE_BACKEND=sqlite
FLYTO_USE_QUEUE=true
FLYTO_WORKER_POOL_SIZE=4
```

Set `FLYTO_WORKER_POOL_SIZE=0` on API-only replicas and run workers separately.
An Enterprise distribution can run API and worker replicas against a shared
queue adapter:

```text
QUEUE_BACKEND=redis
FLYTO_QUEUE_FACTORY=flyto2_enterprise_extensions.redis:create_queue
FLYTO_PROVIDER_MODULE_ALLOWLIST=flyto2_enterprise_extensions
```

Start an independent worker:

```bash
python src/ui/web/backend/main_worker.py --concurrency 4
```

Shared adapters must implement leases, heartbeats, idempotency, retry limits,
atomic dequeue, cancellation, cleanup, and health reporting from
`QueueInterface`.

A shared queue alone is insufficient. Workers also need the edition's shared
execution/data provider. SQLite files must never be shared over NFS or mounted
by multiple hosts.

## Secret Backends

Local AES-256-GCM:

```text
FLYTO_KEY_BACKEND=local
FLYTO_ENCRYPTION_KEY=<at-least-32-random-characters>
FLYTO_KEY_SALT=<unique-deployment-salt>
FLYTO_ENCRYPTION_KEY_VERSION=1
```

Vault Transit:

```text
FLYTO_KEY_BACKEND=vault
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN_FILE=/run/secrets/vault-token
VAULT_CACERT=/run/secrets/vault-ca.pem
VAULT_NAMESPACE=<optional-namespace>
VAULT_TRANSIT_MOUNT_POINT=transit
VAULT_TRANSIT_KEY=flyto-credentials
```

AWS KMS:

```text
FLYTO_KEY_BACKEND=kms
AWS_KMS_KEY_ID=arn:aws:kms:region:account:key/key-id
AWS_REGION=us-east-1
FLYTO_KMS_ALLOW_LEGACY_CIPHERTEXT=false
```

Other KMS, key-vault, or HSM providers:

```text
FLYTO_KEY_BACKEND=custom
FLYTO_KEY_BACKEND_FACTORY=flyto2_enterprise_extensions.keys:create_backend
FLYTO_PROVIDER_MODULE_ALLOWLIST=flyto2_enterprise_extensions
```

KMS uses an authenticated envelope with an application encryption context.
Use workload identity or an ambient IAM role; do not place static AWS
credentials in the Flow environment file. Vault requires HTTPS except for an
explicit loopback-only development override. Vault Agent token files, private
CA bundles, and namespaces are supported. A configured remote key backend
must complete an encrypt/decrypt readiness round trip and never falls back to
a local key.

The custom factory must return a `KeyManagementBackend`. Its module must match
the provider allowlist exactly or be inside an allowlisted package. Private
factory names, malformed imports, partial implementations, and failed
readiness checks stop startup.

Legacy KMS envelopes without an encryption context are rejected by default.
Set `FLYTO_KMS_ALLOW_LEGACY_CIPHERTEXT=true` only during a controlled
re-encryption migration, then disable it.

Local key rotation is deployment-coordinated. Increase
`FLYTO_ENCRYPTION_KEY_VERSION`, set the new key, and retain prior keys in
`FLYTO_ENCRYPTION_PREVIOUS_KEYS` until all old ciphertext has been replaced.
Vault and KMS rotation remains provider-managed.

## Audit Export

Export the local tamper-evident audit chain:

```bash
python scripts/flow_ops.py export-audit \
  --database /data/flyto/executions.db \
  --format jsonl \
  --output /exports/flyto-audit.jsonl
```

Secret-like fields are redacted before persistence. Every event binds the
previous hash, sequence, timestamp, actor, resource, result, and details.

## Alerts

Prometheus metrics remain available at `/api/metrics/`. Optional alert
webhooks require HTTPS:

```text
FLYTO_ALERT_WEBHOOK_URL=https://alerts.example.com/flyto
FLYTO_ALERT_WEBHOOK_ALLOWED_HOSTS=alerts.example.com
FLYTO_ALERT_WEBHOOK_SECRET=replace-with-a-secret
```

Webhook requests include `X-Flyto2-Signature` with an HMAC-SHA256 digest when
a signing secret is configured. Redirects are rejected and every configured
webhook host must be allowlisted.

Prometheus metrics are exposed locally and traces use SQLite by default.
Enterprise distributions can inject an OTLP or private collector adapter:

```text
FLYTO_TRACE_EXPORTER_FACTORY=flyto2_enterprise_extensions.telemetry:create_exporter
FLYTO_PROVIDER_MODULE_ALLOWLIST=flyto2_enterprise_extensions
```

The factory must return `TraceExporter`. A configured exporter that cannot be
loaded or does not implement the contract fails startup instead of silently
falling back to local storage.

## Load And Recovery Tests

Queue and worker substrate:

```bash
python scripts/load_test.py queue \
  --jobs 50000 \
  --workers 32 \
  --payload-bytes 4096 \
  --min-throughput 100
```

Running service or complete workflow endpoint:

```bash
python scripts/load_test.py http \
  --url https://flow.example.com \
  --path /api/executions/run \
  --method POST \
  --request-file ./load/workflow-request.json \
  --requests 10000 \
  --concurrency 100 \
  --max-error-rate 0.001
```

The command emits `flyto.load-result.v1` JSON with throughput, error rate, and
p50/p95/p99/max latency. The CI smoke profile is intentionally small. Release
qualification must run an environment-sized test with the actual shared
queue, data provider, secret backend, and representative large workflows.
