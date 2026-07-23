# Getting Started

This guide takes a new operator from a published container image to a locally
callable MCP workflow tool.

## Prerequisites

- Docker Engine or Docker Desktop
- enough local storage for the application image, Chromium, and workflow data

Git, Docker Compose, Python 3.12, and Node.js 20 are required only when building
or developing from source.

## 1. Start the Local Application

Pull the reviewed release:

```bash
docker pull docker.io/flyto2/flow:0.1.1
```

Start Flow on the loopback interface with persistent local storage:

```bash
docker run --detach \
  --name flyto-flow \
  --init \
  --restart unless-stopped \
  --shm-size=1g \
  --publish 127.0.0.1:9000:9000 \
  --volume flyto-flow-data:/data/flyto \
  docker.io/flyto2/flow:0.1.1
```

Open <http://127.0.0.1:9000>. The default configuration publishes the service
only on loopback and stores state in the `flyto-flow-data` Docker volume.

Confirm the backend is healthy:

```bash
curl --fail http://127.0.0.1:9000/api/health
```

## 2. Create a Workflow-Backed Tool

On a first run with an empty template library, Flow creates HTTP GET, browser
screenshot, and JSON-to-CSV starters. Open **Templates** to inspect or adapt
one, or follow these steps to create a focused tool from scratch:

1. Open **MCP Studio** from the primary navigation.
2. Select **New tool**. Flow creates a starter workflow with an MCP trigger.
3. Select **Edit workflow**.
4. Give the tool a stable action-oriented name and description.
5. Add the browser, HTTP, file, data, AI, or control-flow steps required for
   one useful outcome.
6. Define trigger input fields instead of accepting an unstructured payload
   when the contract is known.
7. Save and run the workflow with non-sensitive test data.

A focused tool is easier for an agent to select and safer for an operator to
review. Prefer `collect_release_notes` over a vague name such as `automation`.
The [starter template guide](starter-templates.md) documents each seeded
contract, default, output, and network boundary.

## 3. Test the Tool in MCP Studio

Return to **MCP Studio** and refresh the tool list. Select the tool, complete
the generated argument form, and run it.

Before connecting an agent, verify:

- required inputs and input types are correct;
- the response is useful without reading internal logs;
- failure output identifies the failed operation without exposing credentials;
- sensitive side effects stop at an approval checkpoint;
- the audit view identifies the source workflow and expected contract.

## 4. Connect an MCP Client

Use the **Connect** tab to copy a configuration generated from the running
instance. The local stdio configuration launches the bridge from
`src/ui/web/backend` and points it at `http://127.0.0.1:9000`.

See [`mcp-studio.md`](mcp-studio.md) for Codex, Claude Code, desktop-client, and
Streamable HTTP examples.

## Stop and Restart

Stop the application:

```bash
docker stop flyto-flow
```

Start it again:

```bash
docker start flyto-flow
```

Do not remove the `flyto-flow-data` volume unless the local workspace is
intentionally being deleted.

## Back Up Local Data

The Compose deployment uses the named `flyto-flow-data` volume. Stop writes
before taking a consistent volume-level backup. Backup and restore mechanics
depend on the container platform; validate a restore in a disposable
environment before relying on it.

At minimum, retain:

- the exact application revision or image digest;
- any reviewed environment configuration without publishing its secrets;
- the complete application data volume;
- the active `flyto-core` artifact version and trusted digest.

## Update Flow

Read the release notes and pull the next exact version. Stop and replace the
container while retaining the named data volume:

```bash
docker pull docker.io/flyto2/flow:<version>
docker stop flyto-flow
docker rm flyto-flow
docker run --detach \
  --name flyto-flow \
  --init \
  --restart unless-stopped \
  --shm-size=1g \
  --publish 127.0.0.1:9000:9000 \
  --volume flyto-flow-data:/data/flyto \
  docker.io/flyto2/flow:<version>
```

Use the digest published by the release workflow when an environment requires
an immutable deployment reference.

## Update `flyto-core` Offline

Obtain a trusted wheel and SHA-256 digest on a connected machine, transfer both
to the Flow operator, and upload the artifact:

```bash
curl -X POST http://127.0.0.1:9000/api/core/upload \
  -H "X-Flyto-Core-SHA256: <64-character-sha256>" \
  -F "file=@flyto_core-<version>-py3-none-any.whl"
```

The importer does not invoke `pip` or contact PyPI. Restart the application
after a successful activation so every worker uses the same runtime.

## Build from Source

Clone the repository, create the reviewed local environment file, and build the
same Dockerfile used by the release workflow:

```bash
cp install/.env.ce.example install/.env.ce
docker compose --env-file install/.env.ce -f install/docker-compose.ce.yml up --build
```

The Compose deployment uses the same loopback port and
`flyto-flow-data` volume as the published-image command.

## Direct Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r src/ui/web/backend/requirements-ce.lock
npm --prefix src/ui/web/frontend ci
npm --prefix src/ui/web/frontend run build
python src/ui/web/backend/main_offline.py --host 127.0.0.1 --port 9000 --no-reload
```

Run repository checks before opening a pull request:

```bash
make verify
flyto-index scan .
flyto-index verify . --strict
```

## Network Exposure

Do not change the bind address merely to make MCP available remotely. Place the
service behind an operator-controlled reverse proxy with TLS, authentication,
origin policy, request limits, and network restrictions. Configure
`FLYTO_FLOW_MCP_TOKEN` for non-loopback MCP access and explicitly review
`FLYTO_MCP_ALLOWED_ORIGINS` when a browser client uses another origin.

The bearer token is an operator access guard, not a hosted account system.

## Troubleshooting

### The page does not load

Check container logs and confirm port `9000` is not occupied. Keep the public
bind on `127.0.0.1` unless remote exposure is intentional.

### MCP Studio shows no tools

Confirm the workflow is saved, contains `flow.trigger`, uses
`trigger_type: mcp`, and has a non-empty tool name. Refresh MCP Studio after a
save.

### A tool call fails

Run the workflow from the builder with the same inputs. Inspect execution
history and evidence, verify credentials are stored as credentials rather than
literal workflow text, and confirm any external service is reachable from the
container.

### The core runtime is unavailable

Check the core status endpoint and the active artifact. Re-import a trusted
wheel with its digest; never add an automatic package download to work around
an offline installation problem.
