# Enterprise Readiness

Flyto2 Flow keeps one portable workflow and connection model across local,
offline, self-hosted Enterprise, and hosted deployments. The CE appliance
remains accountless. Private editions inject identity, provisioning, shared
queue, and managed-secret adapters through tested provider contracts instead
of copying hosted source into this repository.

## Capability Matrix

| Capability | Shared implementation | Edition boundary |
| --- | --- | --- |
| Identity | OIDC and SAML 2.0 contracts with protocol validation | Concrete IdP redirects, assertions, and sessions stay in Enterprise or Cloud |
| Provisioning | Organization-scoped SCIM 2.0 CRUD contracts | SCIM routes and tenant storage stay in Enterprise or Cloud |
| Authorization | Fail-closed organization/workspace RBAC engine | Identity middleware supplies `PrincipalContext` |
| Queue | Lease, heartbeat, retry, idempotency, worker, and external queue contracts | SQLite is single-appliance; HA requires an allowlisted shared adapter |
| Credentials | AES-256-GCM, Vault Transit, AWS KMS, and an allowlisted KMS/HSM provider port | Operators supply local keys, Vault auth, workload IAM, or an edition-owned provider |
| Audit | Transactional tamper-evident chain, verification, JSONL, and CSV | Private editions may inject a SIEM/compliance sink |
| Connections | Built-in catalog, revisioned profiles, secret references, policy, and API | Private editions may inject tenant stores, secret resolvers, and transports |
| Extensions | Strict schema, digests, size limits, Ed25519, revocation, permission grants, and template-pack semantic validation | Runtime plugins remain process-isolated by Flyto2 Core |
| Observability | Prometheus, traces, queue metrics, alert scheduler, and signed HTTPS webhooks | External scrape, collector, and alert routing are operator-owned |
| Operations | Transactional migrations, verified backup/restore, compatibility and load tooling | Deployment automation owns snapshots, rollout, and rollback orchestration |
| Release | One `VERSION`, native AMD64/ARM64 tests, SBOM, provenance, and blocking scans | A strict SemVer Git tag is the only image publication trigger |

The table distinguishes code that is present in this repository from adapters
that cannot be included without violating Flow CE's accountless,
single-workspace boundary. A contract is not presented as a working SSO or HA
deployment until its edition-specific adapter passes the conformance list
below.

## Connections And Credentials

The local API exposes:

- `GET /api/connections/catalog`
- `GET /api/connections/profiles`
- `PUT /api/connections/profiles/{profile_id}`
- `DELETE /api/connections/profiles/{profile_id}`
- `POST /api/connections/profiles/{profile_id}/validate`

Profiles store non-secret configuration and credential references. Sensitive
keys such as passwords, tokens, API keys, private keys, and webhook URLs are
rejected from profile configuration. Optimistic revisions prevent lost
updates. A profile policy may restrict operations, workflows, hosts, ports,
protocols, transport kinds, and access to private networks.

The built-in catalog covers HTTP APIs, PostgreSQL, Slack, SMTP, and
OpenAI-compatible APIs, plus portable GitHub, GitLab, S3-compatible storage,
and MCP Streamable HTTP definitions. Extension manifests can add namespaced
connection types. Catalog presence does not imply a built-in CE transport.
A private transport package can replace the complete
`ConnectionRuntime` through an allowlisted factory without modifying workflow
documents.

## Identity And Provisioning

`gateway.providers.identity.contracts` defines immutable SSO configuration,
principal, SCIM principal, and SCIM group shapes. It also defines the
`IdentityProvider` and `ProvisioningProvider` runtime protocols.

The contract supports both OIDC and SAML 2.0. SSO configuration stores only a
secret reference. A concrete adapter owns redirect, assertion, token,
certificate, replay, audience, issuer, and session validation.

The SCIM contract requires every operation to include an organization ID.
Private editions expose SCIM HTTP routes and implement storage. Flow CE does
not expose account-management routes or persist enterprise membership.

## Tenant And RBAC Isolation

`RBACAccessProvider` evaluates an immutable `PrincipalContext` against an
organization and optional workspace. Unknown roles, permissions, inactive
principals, cross-organization requests, and cross-workspace requests fail
closed.

Built-in roles provide viewer, editor, operator, workspace-admin, and
organization-admin baselines. Private editions may add roles without changing
the workflow or API resource model.

## Provider Injection

An external package can return a `ProviderBundle` containing access, audit,
data, identity, provisioning, queue, and secret adapters. Queue and connection
composition roots accept explicit `module:factory` configuration, and the
module must match `FLYTO_PROVIDER_MODULE_ALLOWLIST`.

Other key-management systems, including Azure Key Vault, Google Cloud KMS, and
HSM-backed implementations, use `FLYTO_KEY_BACKEND=custom` with an allowlisted
`FLYTO_KEY_BACKEND_FACTORY`. The factory must return a complete
`KeyManagementBackend` and pass its startup readiness check. Failure never
falls back to local encryption.

The default allowlist is `flyto2_enterprise_extensions`. CE does not load an
external provider bundle and retains its accountless startup behavior.

## Conformance Requirements

An Enterprise distribution is not release-ready until it proves:

- OIDC or SAML login, logout, replay rejection, issuer, audience, and expiry
  validation;
- SCIM create, update, deactivate, group membership, pagination, and
  organization isolation;
- cross-organization and cross-workspace authorization denial;
- queue lease recovery, duplicate delivery, idempotency, and graceful worker
  shutdown;
- Vault or KMS outage behavior and credential rotation;
- backup, restore, migration, rollback, and compatibility drills;
- audit hash or sink integrity and redaction;
- signed extension rejection and trusted-key rotation;
- template-pack digest and semantic rejection;
- native AMD64 and ARM64 container health checks.

The CE tests cover the shared contracts. Adapter-specific integration tests
belong to the repository that owns the concrete adapter.

## Horizontal Scaling Boundary

`main_worker.py` is a signal-aware standalone worker and the API process can
run with `FLYTO_WORKER_POOL_SIZE=0`. Multiple API and worker replicas require
both:

1. an allowlisted shared `QueueInterface` implementation; and
2. an edition-owned shared execution/data provider.

SQLite remains intentionally limited to one appliance. Pointing several hosts
at one SQLite file or configuring only a shared queue is unsupported and is
not described as HA.
