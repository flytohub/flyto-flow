# Flyto2 Cloud Edition Matrix

| Profile | Edition | Deployment | Auth | License | Cloud Bridge |
| --- | --- | --- | --- | --- | --- |
| `cloud_saas` | SaaS | hosted | Flyto2 account / OIDC | subscription | managed |
| `cloud_ce` | Open Source CE | local offline / self-host | local JWT | CE export license | disabled by default |
| `cloud_enterprise_selfhost` | Self-host Enterprise | customer infra | enterprise IdP or local JWT fallback | commercial enterprise | optional signed token |
| `cloud_enterprise_airgap` | Enterprise Airgap | airgap | enterprise IdP or local JWT fallback | signed offline license | disabled |

## Product Roles

Flyto2 Cloud is the workflow/template/MCP factory and automation control plane.
Public marketplace, Stripe billing, creator payouts, and managed runner fleet
are SaaS-only. Enterprise profiles expose private registries and audit/RBAC
controls without requiring SaaS marketplace services.

Flyto2 Warroom is the security war room, verification, evidence, remediation,
and runtime/security workflow product.

## Shared Contract

Both products use `flyto.editions.v1`:

- `product`
- `edition`
- `deployment`
- `auth_mode`
- `license_mode`
- `capabilities`
- `pages`
- `bridge_policy`

UI routes, API routes, MCP tools, and bridge actions must default deny unless
the backend capability response explicitly exposes them.

## Auth Boundary

Cloud and Warroom do not share password databases.

CE defaults to local JWT per product. SaaS and enterprise can share an IdP or
Flyto2 account. Warroom-to-Cloud automation uses signed short-lived bridge or
bundle tokens. `auth=none` is only valid for loopback single-user flows with a
local sidecar secret.
