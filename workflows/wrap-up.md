# Wrap-up Workflow

1. Run focused tests, documentation checks, and the required release gates.
2. Update `STATE.md`, `CHANGELOG.md`, `tasks.md`, decisions, or a handoff when
   their durable facts changed.
3. Confirm no credentials, local databases, evidence, indexes, or build output
   entered the commit.
4. Review the final diff and verify local `main` aligns with `origin/main`
   after push.
