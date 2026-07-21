# Flyto2 Cloud Open Core

Flyto2 Cloud CE is the self-hosted workflow and MCP control plane. It is designed
to run without a Flyto2 SaaS dependency.

## CE Scope

CE includes:

- Workflow builder and private template storage.
- Local/offline execution.
- MCP stdio and Streamable HTTP workflow tools.
- Local JWT auth with first-run admin setup.
- SQLite storage with a persistent Docker volume.
- Template import.
- Signed Flyto2 Warroom bundle inbox.
- UI approve flow that promotes a verified Warroom bundle into private MCP-ready templates.

CE and Enterprise deployments do not require public marketplace, Stripe,
Firebase, hosted analytics, or managed runners. Hosted marketplace publishing
and monetization stay SaaS-only.

## Private Scope

The CE export excludes:

- Stripe billing and subscription mutation.
- Creator payout, wallet, seller payout, and hosted marketplace seller backend.
- Managed runner fleet and SaaS job plane.
- Commercial AI/pro modules.
- Enterprise license signer and offline license minting.
- SaaS-only production config, telemetry write keys, and deployment metadata.

## Edition Contract

Cloud and Warroom share `flyto.editions.v1`. Cloud exposes:

- `cloud_saas`
- `cloud_ce`
- `cloud_enterprise_selfhost`
- `cloud_enterprise_airgap`

The backend capability response is the source of truth for pages, APIs, MCP
tools, and bridge actions. Frontend fallback access is intentionally minimal.

## Warroom Bundle Inbox

Warroom drops a signed `flyto-bundle.yaml` into `FLYTO_WARROOM_IMPORT_DIR`.
Cloud scans only metadata, validates the signature, checks hashes, rejects
path traversal and stored secret fields, and then shows the bundle as pending.

Dropped folders are never executed directly. A user must approve the pending
bundle in the UI before Cloud promotes it into private templates and exposes
MCP tools.

## Release Boundary

Generate and verify the same tree that is eligible for publication:

```bash
python scripts/export_cloud_ce.py out/flyto-cloud-ce
python scripts/audit-cloud-ce-boundary.py out/flyto-cloud-ce --release-tree
```

The exporter uses an explicit include/deny manifest and applies the public
`ce/` overlay. The release audit verifies every exported file hash and fails
closed when private paths, hosted implementation markers, assigned hosted
secrets, symlinks, or required release files escape into the CE tree.
