# Tasks

This is the maintainer work queue. It contains repository-ready outcomes, not
private product plans or date commitments.

## P0: Release Integrity

- [ ] Tag a release only after `make verify`, strict Flyto2 Indexer verification,
  and the CE container build pass on the release revision.
- [ ] Document backup, migration, validation, and rollback for any release that
  changes stored data or requires operator action.
- [ ] Keep `FLOW_CLOUD_SYNC.json` complete and reject Cloud-only code in every
  shared path.

## P1: First Success

- [ ] Add a deterministic HTTP-to-structured-output example with no external
  credential requirement.
- [ ] Add a browser extraction example with sanitized fixtures and expected
  evidence artifacts.
- [ ] Exercise install, health check, starter-tool creation, and MCP discovery in
  a release smoke test.
- [ ] Record a short current-product demonstration when the first-run flow
  changes materially.

## P1: MCP Reliability

- [ ] Add compatibility tests for every supported protocol version.
- [ ] Test generated client configurations against their supported clients.
- [ ] Surface invalid or duplicate MCP tool names before save.
- [ ] Make risk, approval, and evidence settings explicit in the trigger editor.

## P2: Community

- [ ] Define a recipe contribution checklist covering provenance, permissions,
  fixtures, expected output, and license.
- [ ] Curate `good first issue` candidates that can be completed without hosted
  product context.
- [ ] Publish a stable workflow-package specification before accepting a broad
  recipe library.
- [ ] Add a maintainer-reviewed showcase section only after real external uses
  can be linked.

## P2: Maintainability

- [x] Adopt the complete Flyto2 project-memory and documentation contract.
- [ ] Reduce Indexer complexity hotspots in isolated behavior-preserving pull
  requests.
- [ ] Add architecture references to runtime, evidence, replay, and provider
  boundaries with low documentation coverage.
- [ ] Keep frontend localization, mobile layout, accessibility, and bundle
  checks in release verification.

## Definition of Done

A task is complete when:

1. user-visible behavior and edition ownership are explicit;
2. implementation and focused tests land together;
3. public documentation describes the actual behavior and limits;
4. `make verify` and `flyto-index verify . --strict` pass;
5. migration and rollback are documented when relevant;
6. every commit contains the required sign-off and CLA trailers.
