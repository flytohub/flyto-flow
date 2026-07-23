# Flow / Cloud Reciprocal Sync

Flyto2 Flow and Flyto2 Cloud are one product family, not independent forks.
Flow remains the clean accountless and offline baseline. Cloud adds hosted and
commercial capabilities downstream. Generic UI fixes can move in either
direction, but only through a narrow shared-file contract.

## Contract

`FLOW_CLOUD_SYNC.json` is the machine-readable allowlist. A file not listed
there is never copied automatically. In particular, authentication, users,
organizations, collaboration, marketplace, billing, telemetry, Firebase,
managed runners, and Cloud routing remain Cloud-only even when a similarly
named Flow file exists.

The allowlist covers the edition-neutral workflow canvas, MCP Studio view,
model, HTTP client, styles, focused tests, and the Header interaction stylesheet.
Each edition owns its router, navigation component, authentication interceptor,
backend composition, and runtime status payload. Both navigation components
must consume the shared class contract, so hover, active, mobile, and dropdown
states remain visually identical without copying hosted concerns into Flow.

## Propagation

```text
Flow main change
  -> optional repository dispatch
  -> Cloud scheduled fallback
  -> Flow-to-Cloud sync pull request
  -> Cloud tests and merge

Cloud main shared-file change
  -> Cloud sync workflow
  -> Cloud-to-Flow backport pull request
  -> Flow purity, license, tests, container, and CodeQL
  -> reviewed or policy-authorized auto-merge
```

No workflow force-pushes or directly overwrites either `main` branch. A pull
request with branch protection is the synchronization unit. Content-equal
changes are no-ops, which prevents loops when a synchronization PR merges.

## Authority and conflicts

- Flow is authoritative for offline behavior, public APIs, visual baseline,
  local data, packaging, and all files after a successful backport.
- Cloud is authoritative for hosted composition and Cloud-only source.
- A conflict never resolves automatically. The sync PR stays open and the
  shared fix is reworked against Flow first.
- Changing the allowlist requires matching changes in both repositories and
  CODEOWNER review.

## Required credentials

Cloud holds a least-privilege `FLOW_SYNC_TOKEN` or GitHub App credential able
to create branches and pull requests in both repositories. The legacy
`PUBLIC_RELEASE_TOKEN` is a temporary Cloud-only fallback and should be rotated
out. Flow may hold a dispatch-only `FLOW_SYNC_TOKEN` for immediate notification;
without it, Cloud's scheduled poll still discovers Flow changes.

Set `FLOW_SYNC_AUTO_MERGE=true` only after both repositories require their
documented CI and CodeQL checks on protected `main`. Even then, the workflow
uses GitHub auto-merge rather than bypassing branch protection.

## Security properties

- Secrets exist only as GitHub Actions secrets, never in this public tree.
- Repository-dispatch data is not used as a checkout ref or shell command.
- Paths are fixed by the manifest, checked for traversal, and required to exist
  in both repositories.
- Cloud-to-Flow candidates are scanned for hosted markers before a branch is
  pushed and then pass the complete Flow purity gate.
- The license and CLA policy is release-blocking.

The operational runbook and ownership handoff live in the private
`flyto-cloud` repository.
