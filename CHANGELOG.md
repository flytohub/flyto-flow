# Changelog

All notable changes to the current source-available Flyto2 Flow line are
recorded here. Historical Apache-2.0 revisions remain governed by
`LICENSE_HISTORY.md`.

## Unreleased

No changes yet.

## 0.1.1 - 2026-07-24

### Added

- Organization, workspace, and resource-scoped authorization contracts for
  OIDC, SAML, SCIM, role bindings, and fail-closed enterprise provider
  injection.
- Revisioned connection definitions and credential references for HTTP,
  PostgreSQL, Slack, SMTP, OpenAI, GitHub, GitLab, S3, and MCP transports.
- Queue leases, worker recovery, external queue providers, standalone workers,
  and repeatable concurrency load tests.
- Local AES-GCM, Vault Transit, AWS KMS, and allowlisted external key-management
  backends with readiness checks and fail-closed startup.
- Signed extension manifests, trusted and revoked key handling, permission
  grants, artifact digest verification, and an official starter template pack.
- Transactional migrations, integrity-checked backup and restore, compatibility
  enforcement, audit hash chains, metrics, traces, and signed alert delivery.
- Native AMD64 and ARM64 release candidates, blocking vulnerability scans,
  per-platform SBOM and provenance attestations, and a verified
  multi-architecture manifest.
- Complete Flyto2 project-memory scaffold, documentation index, feature/source
  manifest, and repeatable agent workflows.
- Source-backed feature reference covering the visual builder, local gateway,
  Flyto2 Core execution, MCP Studio, evidence, packaging, and explicit
  non-features.
- Pain-led repository introduction, outcome-focused quick start, use cases,
  MCP client guidance, architecture, project state, roadmap, task, and decision
  documents.
- Structured bug and feature issue forms that collect reproducible evidence and
  enforce the self-hosted edition boundary.
- Documentation integrity checks for required public files, local links,
  Flyto2 branding, and `@flyto2.com` contact domains.
- Visual MCP Studio for discovering workflow tools, generating typed inputs,
  making live calls, configuring agent clients, and reviewing audit metadata.
- Additive MCP metadata for source workflows, contract versions, fingerprints,
  risk levels, approval policies, and evidence references.
- Repository-level guidance for contributors and coding agents.
- Idempotent first-run HTTP GET, browser screenshot, and JSON-to-CSV MCP
  starter workflows for empty local workspaces, with maintained contracts and
  operator guidance.
- Deterministic Python, frontend, API-route, and environment reference pages,
  with a CI freshness gate that rejects undocumented source drift.

### Changed

- Established one authoritative root `VERSION`, synchronized frontend package
  metadata, runtime version loading, release tag validation, and version-aware
  container smoke tests.
- Locked CE runtime dependencies with hashes and made extension verification
  run only after the locked runtime is installed.
- Made the workflow-to-MCP value, local-first access model, intended audience,
  and deliberate product limits explicit on the repository first screen.
- Added the documentation integrity check to local and CI verification.
- Documented the exact Flow-to-Cloud synchronization allowlist and ownership
  boundary for the shared MCP Studio.
- Aligned the Flow Header with Cloud's existing logo sizing, navigation flow,
  responsive menu, and class-based dark hover behavior. Header interaction
  styles now synchronize as one byte-identical visual contract while routes and
  product actions remain edition-owned.
- Allowed browser clients on one loopback port to call the local API on another
  loopback port while continuing to reject non-loopback origins.
- Preserved accountless MCP access through the loopback-only Compose port with
  an explicit, fail-closed Docker bridge trust flag.
- Consolidated saved workflow definitions on the local template store and
  removed the disconnected workflow CRUD, version, and execute wrappers that
  the Builder never used.
- Persisted execution records under the Docker data volume, resolved
  error-workflow links from saved templates, and restored alert metrics
  collection through the current collector API.
- Corrected scoped dark-mode selectors for shared controls and template menus,
  and aligned the shared MCP Studio tab/content spacing in Flow and Cloud.

## 0.1.0 - 2026-07-23 [Superseded]

This release remains immutable for provenance, but should not be used. Its
published source still reported internal version `0.3.1`, and its Docker
manifest did not include `linux/arm64`. Version `0.1.1` is the first release
enforced by the authoritative version contract and native multi-architecture
publication gate.
