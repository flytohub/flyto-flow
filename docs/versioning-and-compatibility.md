# Versioning And Compatibility

Flyto2 Cloud CE uses semantic versioning for published releases. The
`flyto.editions.v1` contract is the stable boundary shared by the backend,
frontend, MCP tools, and signed Warroom bundle imports.

## Compatibility Policy

- Patch releases preserve API behavior and stored-data compatibility.
- Minor releases may add routes, fields, capabilities, and optional migrations.
- Major releases may remove deprecated behavior or require a documented data
  migration.
- Additive response fields are not breaking changes. Clients must ignore fields
  they do not recognize.
- SQLite schema migrations must be forward-only, restart-safe, and covered by a
  test from the previous supported schema.
- Signed bundle verification may become stricter in any release when required
  to address a security issue.

Breaking changes and operator actions are recorded in release notes. A release
that requires manual migration must include exact backup, migration, validation,
and rollback commands before it can be published.
