# Flyto2 Flow Claude Notes

Read `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `STATE.md`, and
`DECISIONS.md` before changing this repository.

Flyto2 Flow is the source-available, self-hosted visual workflow baseline. Keep
hosted identity, billing, collaboration, marketplace, telemetry, and managed
runner behavior out of this repository. Use the installed `flyto-core` package
for execution and preserve the allowlist in `FLOW_CLOUD_SYNC.json`.

Current revisions use PolyForm Shield and must not be described as
OSI-approved open source. Repository-facing prose stays in English, uses the
Flyto2 name, and uses only `@flyto2.com` public contacts.

Run `make verify` and strict Flyto2 Indexer verification for release-impacting
changes. Frontend work also needs desktop and mobile browser review.

## Project Memory

Keep the root project memory, `docs/README.md`,
`docs/documentation-manifest.json`, `workflows/`, and `handoffs/_registry.md`
current in the same change as behavior, public copy, deployment, or security
boundaries.
