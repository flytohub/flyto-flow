.PHONY: audit backend-smoke contracts docs frontend-verify licenses load-smoke sbom verify

docs:
	python scripts/check_docs.py .
	python scripts/generate_documentation_reference.py --check

audit:
	python scripts/check-ce-purity.py .

contracts:
	python scripts/check_version.py .
	python scripts/check_dependency_lock.py
	python scripts/verify_extensions.py extensions --allow-unsigned

backend-smoke:
	DEPLOYMENT_MODE=offline python -m pytest -q tests/ce

load-smoke:
	python scripts/load_test.py queue --jobs 500 --workers 8 --min-throughput 25

frontend-verify:
	npm --prefix src/ui/web/frontend ci
	npm --prefix src/ui/web/frontend audit --audit-level=high
	npm --prefix src/ui/web/frontend run test:run
	npm --prefix src/ui/web/frontend run build

licenses:
	python scripts/audit_ce_dependencies.py . --python-installed

sbom:
	python scripts/generate_ce_sbom.py . --python-installed

verify: docs audit contracts backend-smoke load-smoke frontend-verify licenses sbom
