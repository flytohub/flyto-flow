# Repository Scripts

Scripts in this directory enforce repository, release, and edition contracts.
They run locally and in CI; do not weaken a check to hide an unexplained
failure.

| Script | Purpose |
| --- | --- |
| `check_docs.py` | Required files, internal links, Flyto2 branding, and contact domains |
| `generate_documentation_reference.py` | Deterministic Python, frontend, API-route, and environment reference generation |
| `check-ce-purity.py` | Reject hosted identity, billing, telemetry, and other Cloud-only signals |
| `check_license_policy.py` | Validate current and historical license declarations |
| `check_contribution_terms.py` | Require sign-off and CLA trailers on contributed commits |
| `audit_ce_dependencies.py` | Audit dependency identities and licenses |
| `generate_ce_sbom.py` | Generate CycloneDX and third-party dependency artifacts |

Run all supported checks through:

```bash
make verify
```

Regenerate source references after changing production symbols, routes, or
environment settings:

```bash
python scripts/generate_documentation_reference.py
```

`make verify` runs the generator with `--check`, so CI rejects source changes
whose committed reference pages are stale.

When changing a script, add a focused regression test under `tests/ce` and run
the script both before and after dependency installation. Repository scanners
must ignore generated dependencies and build artifacts while continuing to
inspect version-controlled public files.
