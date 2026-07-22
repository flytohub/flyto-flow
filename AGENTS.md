# Flyto2 Flow Agent Rules

- Treat this repository as the source-available, self-hosted baseline. Do not
  add hosted identity, billing, marketplace, collaboration, telemetry,
  Firebase, or managed-runner code.
- Read `README.md`, `docs/ce-cloud-boundary.md`, and
  `docs/flow-cloud-sync.md` before changing runtime or shared files.
- Before a deep change, use `flyto-index search` and `flyto-index impact` to
  identify ownership and dependencies. Run `flyto-index verify . --strict`
  after implementation.
- Consume workflow execution through the installed `flyto-core` package. Do
  not vendor or copy the engine into this repository.
- Treat `FLOW_CLOUD_SYNC.json` as the complete shared-file allowlist. Flow is
  canonical for allowlisted files; never synchronize whole repository trees.
- Keep `.flyto-index/`, build output, local databases, credentials, tokens, and
  execution evidence out of commits.
- Keep repository-facing changes in English and preserve the PolyForm Shield,
  contribution, trademark, and historical Apache licensing boundaries.
- Run `make verify` for complete local validation. Frontend changes also
  require desktop and mobile browser review with loading, empty, error, and
  success states.
