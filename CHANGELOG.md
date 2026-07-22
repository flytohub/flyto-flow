# Changelog

All notable changes to the current source-available Flyto2 Flow line are
recorded here. Historical Apache-2.0 revisions remain governed by
`LICENSE_HISTORY.md`.

## Unreleased

### Added

- Visual MCP Studio for discovering workflow tools, generating typed inputs,
  making live calls, configuring agent clients, and reviewing audit metadata.
- Additive MCP metadata for source workflows, contract versions, fingerprints,
  risk levels, approval policies, and evidence references.
- Repository-level guidance for contributors and coding agents.

### Changed

- Documented the exact Flow-to-Cloud synchronization allowlist and ownership
  boundary for the shared MCP Studio.
- Allowed browser clients on one loopback port to call the local API on another
  loopback port while continuing to reject non-loopback origins.
- Preserved accountless MCP access through the loopback-only Compose port with
  an explicit, fail-closed Docker bridge trust flag.
