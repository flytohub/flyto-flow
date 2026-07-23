# Extension SDK

Flyto2 connectors, runtime plugins, and template packs use one supply-chain
manifest: `flyto.extension.v1`.

## Bundle Layout

```text
my-extension/
  flyto-extension.json
  <declared-artifacts>
```

The manifest declares:

- a namespaced ID and strict SemVer version;
- API contract version;
- extension kind: `connector`, `plugin`, or `template-pack`;
- requested permissions;
- every artifact path and SHA-256 digest;
- portable connection-type definitions when applicable;
- an optional Ed25519 signature and signing-key ID.

The schema is
[`extensions/manifest.schema.json`](../extensions/manifest.schema.json). The
official starter template pack is a complete unsigned development fixture.

## Permissions

The v1 permission vocabulary is deliberately small:

- `browser`
- `filesystem.read`
- `filesystem.write`
- `network`
- `process`
- `secrets.read`

Unknown permissions are rejected. Permissions describe the maximum requested
surface. Startup also requires an operator grant for every requested
permission:

```bash
export FLYTO_EXTENSION_PERMISSION_GRANTS='{
  "example.connector": ["network", "secrets.read"]
}'
```

Unlisted permissions fail admission. The manifest grant controls package
admission; Flyto2 Core still applies its process and runtime security controls.

## Verification

Development bundles can be checked without a signature:

```bash
python scripts/verify_extensions.py extensions --allow-unsigned
```

Production verification requires signatures and trusted keys:

```bash
python scripts/sign_extension.py generate-key \
  --private-key ./release-2026.pem \
  --public-key ./release-2026.pub
python scripts/sign_extension.py sign \
  ./my-extension/flyto-extension.json \
  --private-key ./release-2026.pem \
  --key-id release-2026
export FLYTO_EXTENSION_TRUSTED_KEYS='{"release-2026":"BASE64_RAW_ED25519_PUBLIC_KEY"}'
python scripts/verify_extensions.py /opt/flyto/extensions
```

`generate-key` writes the private key with mode `0600`; keep it outside the
bundle and outside source control. `sign` refreshes every declared artifact
digest before signing and replaces the manifest atomically. Store signing keys
in a CI secret manager or hardware-backed signing service for production.

Verification rejects path traversal, missing artifacts, digest drift,
untrusted keys, invalid signatures, unknown permissions, unsupported API
versions, invalid identifiers, duplicate IDs or artifacts, undeclared files,
symlink artifacts, unknown manifest fields, oversized artifacts, revoked
signing keys, and ungranted permissions.

Template packs receive an additional semantic validation pass after bundle
verification. A template pack requests no runtime permissions and declares
exactly one JSON artifact using `flyto.template-pack.v1`. Each template has a
namespaced ID and at least one step. Step IDs and contiguous order indexes
must be unique, and every module uses a namespaced lowercase identifier.

```json
{
  "schema": "flyto.template-pack.v1",
  "templates": [
    {
      "id": "example.http-tool",
      "name": "HTTP Tool",
      "steps": [
        {
          "id": "trigger",
          "module": "flow.trigger",
          "label": "Trigger",
          "params": {},
          "order_index": 0
        }
      ]
    }
  ]
}
```

Verified template packs are admitted before startup seeding. They are imported
only when the local template library is empty; installing a pack never
overwrites user templates.

Multiple trusted keys may be present during rotation. Revoke a compromised key
without removing unrelated trust:

```bash
export FLYTO_EXTENSION_REVOKED_KEYS=release-2025,contractor-key
```

Production startup scans both `FLYTO_EXTENSIONS_DIR` and the plugin directory.
Every non-empty bundle directory must contain `flyto-extension.json`; legacy
unmanaged plugin directories fail closed.

## Connector Contract

A connector manifest can publish portable connection definitions. Runtime
profiles store non-secret configuration and `SecretRef` objects only. The
connection runtime authorizes an operation before resolving credentials and
records an audit event without secret values.

Concrete transport adapters belong to Flyto2 Core or an extension package.
They must not retrieve credentials or decide tenant authorization themselves.

The built-in portable definitions cover `http.api`, `database.postgresql`,
`messaging.slack`, `email.smtp`, `ai.openai`, `source.github`,
`source.gitlab`, `storage.s3`, and `mcp.streamable-http`. Connector manifests
extend this catalog with the same strict JSON Schema contract. Flow CE does
not claim a connector is executable until a transport provider is injected.
