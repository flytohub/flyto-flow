# Flyto2 Cloud CE

Flyto2 Cloud CE is the Apache-2.0 licensed, self-hosted workflow builder and
local execution control plane. It runs without Firebase, hosted billing, a
Flyto2 account, or a managed runner service.

## Included

- Visual workflow and template builder.
- Local execution through `flyto-core`.
- SQLite-backed workflow, template, and execution storage.
- MCP workflow tools over stdio and Streamable HTTP.
- Local JWT authentication and an offline single-user profile.
- Signed Warroom bundle import and explicit approval.

Hosted billing, marketplace monetization, managed runner fleets, enterprise
SSO/RBAC add-ons, and license-signing operations are not part of this tree.

## Run With Docker

Set strong local secrets before exposing the service beyond loopback:

```bash
cp install/.env.ce.example install/.env.ce
# Set FLYTO_OFFLINE_AUTH_SECRET to at least 32 random characters in .env.ce.
docker compose --env-file install/.env.ce -f install/docker-compose.ce.yml up --build
```

Open `http://127.0.0.1:9000`. Persistent application data is stored in the
`flyto-cloud-data` Docker volume.

## Local Development

Requirements: Python 3.12, Node.js 20, and a supported Chromium environment.

```bash
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r src/ui/web/backend/requirements-ce.lock
npm --prefix src/ui/web/frontend ci
npm --prefix src/ui/web/frontend run build
python src/ui/web/backend/main_offline.py --host 127.0.0.1 --port 9000 --no-reload
```

The Python backend expects the frontend build under
`src/ui/web/backend/static`. The Docker build copies it there automatically.

## Verify A Release Tree

```bash
python scripts/audit-cloud-ce-boundary.py . --release-tree
python scripts/audit_ce_dependencies.py .
python scripts/generate_ce_sbom.py . --python-installed
```

`CE_EXPORT.json` binds every published file to its SHA-256 digest and records
the private source commit used to generate the release.

## Contributions

Contributions use the Developer Certificate of Origin. See
`CONTRIBUTING.md`, `DEVELOPER_CERTIFICATE_OF_ORIGIN.md`, and `SECURITY.md`.
Release compatibility rules are documented in
`docs/versioning-and-compatibility.md`.

## License

Apache License 2.0. The license does not grant rights to Flyto2 trademarks.
