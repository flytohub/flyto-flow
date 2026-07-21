# Contributing to Flyto2 Cloud CE

## Before Opening A Change

- Use an issue for behavior changes that alter APIs, stored data, or edition
  contracts.
- Keep CE independent from Firebase, Flyto2 hosted services, commercial
  entitlement services, and enterprise-only packages.
- Never include credentials, customer data, production URLs, or generated
  runtime state.

## Development Checks

Run the checks relevant to your change. Before submitting a release-sensitive
change, run the complete CE gate:

```bash
make verify
```

## Developer Certificate Of Origin

Every commit must include a `Signed-off-by` trailer certifying the Developer
Certificate of Origin:

```bash
git commit --signoff
```

By contributing, you agree that your contribution is licensed under Apache
License 2.0. See `DEVELOPER_CERTIFICATE_OF_ORIGIN.md`.

## Pull Requests

- Explain the user-visible behavior and security impact.
- Add or update tests for changed behavior.
- Document migrations and compatibility changes.
- Keep generated dependency reports and SBOM files out of commits; CI publishes
  them as artifacts.
