# Changelog

All notable changes to the current source-available Flyto2 Flow line are
recorded here. Historical Apache-2.0 revisions remain governed by
`LICENSE_HISTORY.md`.

## Unreleased

### Added

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

### Changed

- Made the workflow-to-MCP value, local-first access model, intended audience,
  and deliberate product limits explicit on the repository first screen.
- Added the documentation integrity check to local and CI verification.
- Documented the exact Flow-to-Cloud synchronization allowlist and ownership
  boundary for the shared MCP Studio.
- Allowed browser clients on one loopback port to call the local API on another
  loopback port while continuing to reject non-loopback origins.
- Preserved accountless MCP access through the loopback-only Compose port with
  an explicit, fail-closed Docker bridge trust flag.
