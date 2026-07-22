# Flyto2 Flow

> Build workflows visually. Publish them as MCP tools.

Flyto2 Flow is an open-source, self-hosted visual workflow and MCP builder powered by `flyto-core`. Combine browser automation, APIs, files, data processing, and control-flow atoms in the UI, test the workflow locally, then expose it as an MCP tool.

## Demo

https://github.com/user-attachments/assets/4357d9a7-0c20-4252-8f72-695da275a3ec

## What Flyto2 Flow Is

```text
Visual atoms → Workflow → Local execution → MCP tool
```

- Visual workflow and template builder
- Local execution through `flyto-core`
- MCP tools over stdio and Streamable HTTP
- SQLite-backed workflows, templates, variables, runs, evidence, and replay
- Chromium and Playwright bundled into the release image
- Offline `flyto-core` updates from an operator-supplied, SHA-256-verified wheel

## Local Means Local

Flyto2 Flow starts without an account, email address, or password. It has one local workspace and contains no Firebase integration, hosted membership system, chat, marketplace, remote collaboration, billing, analytics, telemetry, CDN loader, or automatic package download.

The application itself makes no implicit outbound connection. A workflow can still access a URL when the operator deliberately adds and runs a network-capable atom; that is user-authored workflow behavior, not application telemetry or phone-home traffic.

The default Compose configuration publishes only to `127.0.0.1`. Keep it on loopback unless you deliberately place it behind your own authenticated reverse proxy.

## Run the Complete Offline Image

The image is assembled with `flyto-core`, Playwright, and Chromium already installed. Starting a built image does not download runtime dependencies.

```bash
cp install/.env.ce.example install/.env.ce
docker compose --env-file install/.env.ce -f install/docker-compose.ce.yml up --build
```

Open <http://127.0.0.1:9000>. Application data is stored in the `flyto-flow-data` Docker volume.

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

## Project Boundary

Flyto2 Flow is the clean upstream product. `flyto-cloud` may consume and extend it through documented edition seams, but Cloud-only source must never be merged into this repository. Generic fixes flow from Flyto2 Flow to Flyto2 Cloud; membership, hosted services, billing, chat, telemetry, and remote collaboration stay downstream.

See [CE/Cloud Boundary](docs/ce-cloud-boundary.md), [Edition Matrix](docs/edition-matrix.md), and [Contributing](CONTRIBUTING.md).

## License and Trademark

The current code license is Apache License 2.0. It permits use, modification, distribution, and commercial resale; the license does not grant rights to Flyto2 names or logos. See [TRADEMARKS.md](TRADEMARKS.md) and [Licensing Strategy](docs/licensing-strategy.md) before changing the project license or offering an official commercial distribution.
