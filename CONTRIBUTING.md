# Contributing to Flyto2 Flow

## Before Opening A Change

- Use an issue for behavior changes that alter APIs, stored data, or edition
  contracts.
- Read `docs/ce-cloud-boundary.md`. Hosted product source belongs only in the
  downstream `flyto-cloud` repository.
- Shared fixes land in Flyto2 Flow first and flow downstream. Do not add hosted
  compatibility shims to make a downstream merge easier.
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
- Run `python scripts/check-ce-purity.py` and add boundary regression tests when
  a change touches routes, navigation, dependencies, networking, or packaging.
