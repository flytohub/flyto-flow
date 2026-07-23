# Flyto2 Flow Feature Reference

This reference maps maintained product behavior to implementation, operator
documentation, and verification. Source and tests remain authoritative when a
claim changes.

## Visual Workflow Builder

The Vue frontend under `src/ui/web/frontend` owns workflow editing, module
selection, input forms, execution controls, evidence views, variables, replay,
lineage, metrics, traces, and alerts. It consumes backend contracts and does
not replace runtime validation.

- Operator path: [Getting started](getting-started.md)
- Workflow patterns: [Use cases](use-cases.md)
- Source map: [`src/README.md`](../src/README.md)
- Verification: frontend unit tests and production build in `make verify`

## Local Gateway And Storage

The FastAPI application under `src/ui/web/backend` owns accountless local APIs,
WebSockets, SQLite persistence, local artifacts, and provider selection. The
default deployment binds to loopback and does not require hosted identity.

- Boundaries: [CE and Cloud boundary](ce-cloud-boundary.md)
- Architecture: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- Verification: `python -m pytest -q tests/ce` and CE purity checks

## Flyto2 Core Execution

Workflow execution is delegated to the installed `flyto-core` package. Flow
does not vendor a second engine. Browser-capable releases bundle Playwright and
Chromium; offline Core imports are path-checked, size-limited, digest-verified,
import-tested, and activated atomically.

- Runtime ownership: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- Compatibility: [Versioning and compatibility](versioning-and-compatibility.md)
- Verification: backend smoke, image build, dependency audit, and SBOM gate

## MCP Studio

MCP Studio discovers workflows with an MCP trigger, derives JSON Schema from
their input fields, invokes the source workflow, and exposes source,
fingerprint, risk, approval, and evidence metadata. Streamable HTTP is
loopback-only by default; deliberate non-loopback exposure requires a bearer
token and an authenticated reverse proxy.

- Setup and protocol: [MCP Studio](mcp-studio.md)
- Source map: [`src/README.md`](../src/README.md)
- Verification: MCP-focused backend tests and frontend MCP Studio tests

## Local Evidence And Replay

Execution history, logs, outputs, evidence, replay, lineage, metrics, traces,
and alerts remain in the operator-controlled workspace. The application does
not claim tamper-proof storage or managed retention.

- Usage: [Getting started](getting-started.md)
- Limits: [Edition matrix](edition-matrix.md)
- Verification: CE API smoke and persisted-run tests

## Packaging And Release Evidence

`install/` owns Compose and image inputs. `scripts/` owns purity, documentation,
dependency-license, contribution, and SBOM gates. `FLOW_BOUNDARY.json` and
`FLOW_CLOUD_SYNC.json` are machine-readable product boundaries.

- Script commands: [`scripts/README.md`](../scripts/README.md)
- Test layers: [`tests/README.md`](../tests/README.md)
- Verification: `make verify`

## Explicit Non-Features

The source-available baseline does not include hosted identity, organizations,
billing, marketplace, remote collaboration, application telemetry, CDN-loaded
runtime code, or a managed runner. A workflow can make an outbound request only
when the operator deliberately adds and runs a network-capable step.
