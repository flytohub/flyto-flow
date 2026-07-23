# Architecture

## System Context

Flyto2 Flow is a local full-stack application. The browser UI talks to one
FastAPI process, which owns the local workspace and delegates workflow
execution to the installed `flyto-core` runtime.

```text
MCP client                  Browser
    |                          |
    | Streamable HTTP          | JSON API + WebSocket
    +------------+-------------+
                 |
        FastAPI local gateway
        |        |            |
        |        |            +-- evidence, replay, lineage, observability
        |        +--------------- SQLite repositories and local artifacts
        +------------------------ flyto-core execution runtime
                                      |
                                      +-- Playwright / Chromium when requested
```

## Components

### Frontend

`src/ui/web/frontend` is a Vue 3 and Vite application. It owns visual workflow
editing, MCP Studio, workflow input forms, execution controls, evidence and
debug views, variables, and observability screens. It renders backend state; it
does not replace runtime validation or execution policy.

Flow and Cloud compose separate `AppNavbar.vue` components because their routes,
identity actions, notifications, and entitlements differ. Both consume the
allowlisted `features/navigation/appNavbar.css` visual contract so navigation
states, hover behavior, responsive links, and dropdown items remain identical.

### Local Gateway

`src/ui/web/backend/main_offline.py` assembles the accountless local FastAPI
application. Routes under `src/ui/web/backend/api` expose workflows, templates,
executions, triggers, variables, evidence, replay, lineage, metrics, traces,
alerts, browser interaction, core status, and MCP transport.

The `gateway` package defines provider seams. The baseline selects local data,
access, vector, and audit providers. Hosted providers do not belong in this
repository.

### Execution Runtime

`src/ui/web/backend/services/runtime` validates and runs workflow steps through
the installed `flyto-core` package. Browser-capable workflows use the bundled
Playwright and Chromium runtime. Workflow-authored network calls are explicit
operator behavior.

### MCP Surface

`src/ui/web/backend/mcp_server.py` discovers saved workflows containing a
`flow.trigger` step with `trigger_type: mcp`. It derives JSON Schema from the
trigger's input fields, maps each tool name to its source workflow, and submits
tool calls to the same local execution API used by the product.

`src/ui/web/backend/api/mcp.py` exposes MCP JSON-RPC over Streamable HTTP. It
enforces accepted media types, origin checks, and loopback-only access by
default. The stdio bridge also refuses a non-loopback backend URL.

### Local State

SQLite repositories under `src/ui/web/backend/gateway/storage` hold local
workspace data and execution records. Evidence and replay services retain
operator-inspectable run artifacts. Container deployments keep application
state in the `flyto-flow-data` volume.

## Main Data Flows

### Design and Run

1. The UI loads the module catalog exposed by `flyto-core`.
2. The author assembles and validates a workflow.
3. The backend persists the workflow in the local workspace.
4. A run request is validated and submitted to the execution manager.
5. Status, logs, outputs, and evidence return through APIs and WebSockets.

### Publish as MCP

1. The author adds an MCP trigger and names the tool.
2. The MCP server discovers the saved workflow.
3. Trigger input fields become the tool's JSON Schema.
4. MCP Studio or an external client calls `tools/call`.
5. The server starts the source workflow with the supplied arguments.
6. The response and run evidence remain available for inspection.

## Trust Boundaries

- **Browser to local gateway:** same-origin by default; configured cross-origin
  requests are explicit.
- **MCP client to gateway:** accountless on loopback; a bearer token is required
  when an operator deliberately allows non-loopback access.
- **Gateway to runtime:** an installed local `flyto-core`; no managed runner.
- **Workflow to network:** outbound access exists only when the workflow author
  selects and runs a network-capable step.
- **Offline update boundary:** uploaded wheels are size-limited, archive-path
  checked, package-name checked, digest verified, import tested, and activated
  atomically.
- **Flow to Cloud:** only paths in `FLOW_CLOUD_SYNC.json` may synchronize. Flow
  remains canonical for every allowlisted path, including the Header visual
  contract but not either edition's navigation component.

## Invariants

1. Default published ports remain bound to `127.0.0.1`.
2. The baseline starts without hosted identity or credentials.
3. The application creates no implicit outbound dependency.
4. MCP tool metadata is additive and does not replace the standard tool
   contract.
5. Cloud-only code never enters this repository.
6. Stored-data and API compatibility follow
   [`docs/versioning-and-compatibility.md`](docs/versioning-and-compatibility.md).

## Extension Points

- Add workflow behavior through `flyto-core` modules, not duplicated runtime
  implementations in the UI.
- Add local providers only when they preserve the edition boundary.
- Add MCP metadata additively so standard clients continue to work.
- Add a Flow-to-Cloud shared file only by updating the complete allowlist and
  passing purity checks in both products.

## Verification

`make verify` runs purity, backend smoke, frontend test/build, dependency
license, and SBOM checks. CI adds focused lint, strict Flyto2 Indexer
verification, contribution terms, and a container build. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).
