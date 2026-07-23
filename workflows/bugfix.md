# Bugfix Workflow

1. Reproduce the failure with sanitized local evidence.
2. Trace the owning frontend, gateway, runtime, storage, or MCP boundary.
3. Add a regression test before or with the smallest corrective change.
4. Run focused checks, then `make verify` for release-impacting fixes.
