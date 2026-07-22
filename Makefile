.PHONY: audit backend-smoke frontend-verify licenses sbom verify

audit:
	python scripts/check-ce-purity.py .

backend-smoke:
	DEPLOYMENT_MODE=offline python -m pytest -q tests/ce

frontend-verify:
	npm --prefix src/ui/web/frontend ci
	npm --prefix src/ui/web/frontend audit --audit-level=high
	npm --prefix src/ui/web/frontend run test:run
	npm --prefix src/ui/web/frontend run build

licenses:
	python scripts/audit_ce_dependencies.py . --python-installed

sbom:
	python scripts/generate_ce_sbom.py . --python-installed

verify: audit backend-smoke frontend-verify licenses sbom
