# Flyto2 Flow

> Build workflows visually. Publish them as MCP tools.

Flyto2 Flow is a source-available, self-hosted visual workflow and MCP builder powered by `flyto-core`. Combine browser automation, APIs, files, data processing, and control-flow atoms in the UI, test the workflow locally, then expose it as an MCP tool.

## Demo

https://github.com/user-attachments/assets/4357d9a7-0c20-4252-8f72-695da275a3ec

## Usage

Build or import a workflow, add an MCP trigger, and open **MCP Studio** from
the primary navigation. Select the generated tool, complete the schema-driven
form, run it locally, then use **Connect** to configure Codex, Claude Code, a
desktop client, or another Streamable HTTP client. The **Audit** view explains
the source, contract, risk, approval, and evidence attached to every tool.

## MCP Studio

![MCP Studio showing workflow tools, generated arguments, and a live response](docs/assets/mcp-studio.jpg)

MCP Studio turns a visual workflow into an agent tool without requiring a
custom server. Create a workflow with an MCP trigger, inspect its generated
JSON Schema, call it from the browser, review the response and session history,
then copy a ready-to-use configuration for Codex, Claude Code, desktop clients,
or any Streamable HTTP client.

```text
Design workflow -> expose tool -> test call -> connect agent -> audit evidence
```

Tool metadata records the source workflow, contract version, deterministic
fingerprint, risk level, approval policy, and evidence references. Local Flow
uses a loopback accountless endpoint by default; Flyto2 Cloud presents the same
studio through its authenticated hosted endpoint.

## Architecture

```text
Visual atoms → Workflow → Local execution → MCP tool
```

- Visual workflow and template builder
- Local execution through `flyto-core`
- MCP tools over stdio and Streamable HTTP
- Built-in MCP Studio for discovery, schema forms, live calls, client setup,
  and session audit
- SQLite-backed workflows, templates, variables, runs, evidence, and replay
- Chromium and Playwright bundled into the release image
- Offline `flyto-core` updates from an operator-supplied, SHA-256-verified wheel

## Local Means Local

Flyto2 Flow starts without an account, email address, or password. It has one local workspace and contains no Firebase integration, hosted membership system, chat, marketplace, remote collaboration, billing, analytics, telemetry, CDN loader, or automatic package download.

The application itself makes no implicit outbound connection. A workflow can still access a URL when the operator deliberately adds and runs a network-capable atom; that is user-authored workflow behavior, not application telemetry or phone-home traffic.

The default Compose configuration publishes only to `127.0.0.1`. Keep it on loopback unless you deliberately place it behind your own authenticated reverse proxy.

## Quick Start

The image is assembled with `flyto-core`, Playwright, and Chromium already installed. Starting a built image does not download runtime dependencies.

```bash
cp install/.env.ce.example install/.env.ce
docker compose --env-file install/.env.ce -f install/docker-compose.ce.yml up --build
```

Open <http://127.0.0.1:9000>. Application data is stored in the `flyto-flow-data` Docker volume.

## Configuration

Container defaults are documented in `install/.env.ce.example`; direct-process
defaults are documented in `.env.example`. The server is accountless and bound
to loopback by default. The Compose profile explicitly trusts its private
Docker bridge only while the published port remains bound to `127.0.0.1`. Set
`FLYTO_FLOW_MCP_TOKEN` when an authenticated reverse proxy deliberately exposes
MCP beyond the local machine.

## API

- `GET /api/mcp/status` discovers the local MCP endpoint and protocol metadata.
- `POST /api/mcp` accepts MCP Streamable HTTP JSON-RPC requests.
- `POST /api/core/upload` imports an operator-supplied, verified `flyto-core`
  wheel without contacting a package registry.

## Update `flyto-core` Without Connecting the Appliance

Download a trusted `flyto-core` wheel on another machine, transfer it to the Flyto2 Flow operator, calculate its SHA-256 digest, then import it locally:

```bash
curl -X POST http://127.0.0.1:9000/api/core/upload \
  -H "X-Flyto-Core-SHA256: <64-character-sha256>" \
  -F "file=@flyto_core-<version>-py3-none-any.whl"
```

The importer does not invoke `pip` or contact PyPI. It checks the package name, digest, archive paths, size limits, and a clean `import core` before atomically activating the new version. Restart the container after a successful import so every worker uses the same version.

## Development

Requirements: Python 3.12 and Node.js 20. Docker is the supported way to get the exact browser runtime.

```bash
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r src/ui/web/backend/requirements-ce.lock
npm --prefix src/ui/web/frontend ci
npm --prefix src/ui/web/frontend run build
python src/ui/web/backend/main_offline.py --host 127.0.0.1 --port 9000 --no-reload
```

## Testing

Run the same boundary, backend, frontend, dependency-license, SBOM, and build
checks used by the repository verification workflow:

```bash
make verify
flyto-index scan .
flyto-index verify . --strict
```

## Project Boundary

Flyto2 Flow is the clean canonical baseline. `flyto-cloud` consumes and extends it through documented edition seams, but Cloud-only source must never be merged into this repository. Shared fixes normally flow from Flow to Cloud; a generic fix discovered in Cloud may return only through the allowlisted, purity-gated backport process. Membership, hosted services, billing, chat, telemetry, and remote collaboration stay downstream.

See [CE/Cloud Boundary](docs/ce-cloud-boundary.md), [Flow/Cloud Sync](docs/flow-cloud-sync.md), [Edition Matrix](docs/edition-matrix.md), and [Contributing](CONTRIBUTING.md).

## License and Trademark

Current revisions use the [PolyForm Shield License 1.0.0](LICENSE): you may inspect, use, modify, and distribute the code for permitted purposes, but you may not use it to provide a product or service that competes with Flyto2. This is source-available/fair-code, not OSI-approved open source. Revisions through commit `9398a62` remain Apache-2.0 and cannot be retroactively restricted.

Read [License History](LICENSE_HISTORY.md), [Commercial Licensing](COMMERCIAL_LICENSE.md), [Trademark Policy](TRADEMARKS.md), and the [Licensing Strategy](docs/licensing-strategy.md) before redistribution or commercial use.
