.PHONY: audit backend-smoke docs frontend-verify licenses sbom verify

docs:
	python scripts/check_docs.py .
	python scripts/generate_documentation_reference.py --check

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

verify: docs audit backend-smoke frontend-verify licenses sbom
