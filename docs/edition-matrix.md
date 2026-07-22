# Flyto2 Product Boundary

| Concern | Flyto2 Flow (this repository) | `flyto-cloud` (downstream) |
| --- | --- | --- |
| Workspace | One fixed local workspace | Downstream-defined |
| Account or password | None | Downstream-defined |
| Storage | Local SQLite and local files | May add managed storage |
| Execution | Local `flyto-core` | May add managed execution |
| MCP | Local stdio and loopback HTTP | May add hosted delivery |
| Network behavior | No implicit outbound requests | Downstream-defined |
| Updates | Operator-transferred wheel only | May add managed updates |
| UI source | Shared pages and layout shells | Same Flow files |
| UI extension | Empty additive `@edition` slots | Downstream slot components |

Flyto2 Flow does not implement dormant hosted pages, routes, stores, database
models, or SDK clients. A capability being disabled at runtime is not a clean
boundary; the implementation must be absent from this repository.

Workflow atoms that explicitly access a URL remain valid. Their network access
occurs only when the local operator creates and runs such a workflow and is not
application phone-home behavior.
