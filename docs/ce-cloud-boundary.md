# Flyto2 Flow / Cloud Boundary

## Non-negotiable rule

Flyto2 Flow is the parent implementation. `flyto-cloud` extends it downstream.
Flow must remain useful with the network physically disconnected and must not
contain dormant hosted product source.

## Allowed in Flow

- Visual workflow and template editing
- Local `flyto-core` execution
- Local Chromium and Playwright automation
- Local SQLite data, variables, evidence, logs, traces, alerts, and replay
- Local MCP stdio and loopback HTTP delivery
- Import and export initiated by the operator
- Offline `flyto-core` update from an operator-supplied wheel with SHA-256
  verification
- HTTP, browser, LLM-provider, and similar atoms explicitly configured and run
  by the operator

## Must remain downstream

- Accounts, login, registration, profiles, organizations, members, roles, and
  invitations
- Messaging, chat, support inboxes, issue reporting, and remote collaboration
- Hosted dashboards, model or plugin marketplaces, public publishing, ratings,
  and creator programs
- Billing, subscriptions, payments, wallets, quotas, and entitlements
- Firebase or other hosted identity/data SDKs
- Managed runners, remote job queues, device wake-up, and cloud bridges
- Analytics, behavioral events, crash upload, telemetry, tracking pixels, and
  remote log shipping
- Automatic registry checks, CDN-loaded UI code, or application phone-home
  traffic

These areas are absent source, not disabled features. Do not add placeholder
routes, hidden pages, no-op stores, strings, SDK dependencies, or database
tables for them.

## User-authored network boundary

The application performs no implicit outbound connection. A network-capable
atom can connect only because an operator selected it, supplied its endpoint
and credentials, and ran the workflow. Secrets stay in the local credential
store. This exception does not permit update checks, analytics, remote catalogs,
or hosted fallbacks.

## Runtime packaging

The release image installs `flyto-core`, Playwright, and Chromium during image
build. Startup is offline and fails clearly when the bundled runtime is missing.
An update wheel is transferred by the operator, verified locally, staged, import
checked without `pip`, then atomically activated for the next process start.

## Merge discipline

1. Shared fixes normally land in Flow first.
2. Cloud automatically pulls allowlisted shared paths from Flow after Flow
   `main` changes, using a guarded pull request.
3. A generic shared fix that lands in Cloud `main` may be proposed back to Flow
   only for paths in `FLOW_CLOUD_SYNC.json`. It must pass Flow purity and
   security checks and never writes directly to Flow `main`.
4. Merge conflicts stop automation and are resolved in a reviewed pull
   request. Flow never accepts hosted shims to make synchronization easier.
5. Downstream frontend additions enter through `@edition`; downstream backend
   additions use a separate application entry point and router composition.
6. Every Flow pull request runs `python scripts/check-ce-purity.py` and
   `python scripts/check_license_policy.py`.

`@edition` is an additive seam, not a second application. It may fill the
named navigation, header-action, footer, banner, route, and page-extension
slots. It may not replace shared layout shells or copy a shared page into a
Cloud-only variant. The editions keep separate navigation composition but use
the same allowlisted Header interaction stylesheet. Visual fixes to shared
surfaces always land in Flow first.

See [Flow/Cloud Reciprocal Sync](flow-cloud-sync.md) for triggers, credentials,
conflict handling, loop prevention, and recovery.
