# Versioning and Compatibility

Flyto2 Flow uses semantic versioning for published releases.

- Patch releases preserve API and stored-data behavior.
- Minor releases may add local routes, workflow fields, atoms, and restart-safe
  migrations.
- Major releases may remove deprecated behavior or require a documented data
  migration.
- API clients must ignore unknown additive response fields.
- SQLite migrations are forward-only, idempotent, and tested from the previous
  supported schema.
- A release that requires operator action documents backup, migration,
  validation, and rollback before publication.

`flyto-cloud` pins a compatible Flow release or commit. Downstream code must
consume the documented edition seams and may not require Flow to contain
hosted-only compatibility branches.
