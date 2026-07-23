# Decisions

This log records durable project decisions. New entries are appended; existing
entries are changed only to correct factual errors or link a superseding
decision.

## D-007: Feature Claims Require Source And Verification Ownership

**Status:** accepted

Every maintained product surface is mapped in
`docs/documentation-manifest.json` to its source, durable documentation, tests,
and verification command.

**Why:** a source-available repository earns trust through inspectable behavior
and limits, not by expanding README claims faster than implementation.

**Consequences:** public feature changes update the manifest and feature
reference in the same change; missing memory or ownership files fail the local
documentation gate.

## D-001: The Baseline Is Accountless and Local-First

**Status:** accepted

The source-available baseline starts with one local workspace and no user
identity. Default network binding is loopback. Hosted identity, organizations,
billing, telemetry, remote collaboration, and managed execution remain outside
this repository.

**Why:** self-hosting is not meaningful when startup or normal operation still
depends on a vendor control plane.

**Consequences:** features that require hosted identity belong downstream;
local security depends on host access and explicit operator exposure controls.

## D-002: Workflows Are the Canonical MCP Tool Source

**Status:** accepted

An MCP tool is derived from a saved workflow containing a `flow.trigger` with
`trigger_type: mcp`. Trigger input fields generate JSON Schema, and tool calls
execute the source workflow.

**Why:** a generated contract prevents a hand-maintained MCP server from
drifting away from the workflow it invokes.

**Consequences:** input-contract changes must be reviewed as tool API changes;
tool names and schemas need compatibility tests.

## D-003: MCP HTTP Is Loopback-Only by Default

**Status:** accepted

Loopback clients may use the local MCP endpoint without an account. A
non-loopback request is rejected unless the operator configures an explicit
bearer token. Browser origins are independently checked.

**Why:** zero-account local use should remain simple without turning the local
tool endpoint into an unauthenticated network service.

**Consequences:** remote operation requires deliberate proxy, TLS,
authentication, origin, and network policy managed by the operator.

## D-004: Flow Is Canonical for Shared Baseline Files

**Status:** accepted

`FLOW_CLOUD_SYNC.json` is the complete synchronization allowlist. Shared fixes
normally move from Flow to Cloud. A generic fix discovered downstream may
return only through the documented, purity-gated backport process.

**Why:** bidirectional copying without ownership rules silently imports hosted
dependencies into the baseline.

**Consequences:** each allowlisted path has one source of truth; Cloud-only
source never enters this repository.

## D-005: Runtime Updates Are Operator-Supplied and Verified

**Status:** accepted

The appliance does not automatically download `flyto-core`. An operator may
upload a wheel with an expected SHA-256 digest; the importer validates package
identity, archive paths, limits, and importability before atomic activation.

**Why:** an offline-capable product cannot make a package registry part of its
startup trust chain.

**Consequences:** operators are responsible for obtaining a trusted artifact
and digest; runtime updates require an application restart.

## D-006: Current Revisions Are Source-Available

**Status:** accepted

Current revisions use PolyForm Shield. Historical revisions through `9398a62`
remain Apache-2.0.

**Why:** the project protects the hosted product boundary while preserving
source inspection, modification, and permitted self-hosted use.

**Consequences:** current code must not be marketed as OSI-approved open
source. Any future license change requires an explicit legal and product
decision; documentation cannot make it implicitly.

## D-008: Header Visuals Are Shared, Composition Is Edition-Owned

**Status:** accepted

Flow and Cloud keep separate `AppNavbar.vue` components for edition-specific
routes and actions. The navigation interaction styles live in the byte-identical
allowlisted `features/navigation/appNavbar.css` file, with Flow as canonical.

**Why:** the products must look and behave like one family without copying
hosted identity, billing, organization, notification, or entitlement logic into
the offline baseline.

**Consequences:** generic Header style changes land in Flow and synchronize
through the guarded contract. Edition-specific menu entries remain local, and
both components must use the shared class names and pass responsive review.
