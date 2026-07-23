"""Tests for the shared Flow/Cloud repository synchronization contract."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_flow_cloud_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_flow_cloud_contract", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class FlowCloudContractTests(unittest.TestCase):
    def _fixture(self, parent: Path, name: str) -> Path:
        root = parent / name
        manifest = json.loads((ROOT / "FLOW_CLOUD_SYNC.json").read_text(encoding="utf-8"))
        for relative in manifest["shared_paths"]:
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        return root

    @staticmethod
    def _manifest(root: Path) -> dict:
        return json.loads((root / "FLOW_CLOUD_SYNC.json").read_text(encoding="utf-8"))

    @staticmethod
    def _write_manifest(root: Path, manifest: dict) -> None:
        (root / "FLOW_CLOUD_SYNC.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_repository_contract_is_valid(self) -> None:
        result = VALIDATOR.validate_contract(ROOT)

        self.assertTrue(result["ok"])
        self.assertEqual(result["contractVersion"], 2)
        self.assertEqual(len(result["manifestSha256"]), 64)

    def test_connection_injection_contract_is_shared(self) -> None:
        manifest = self._manifest(ROOT)

        self.assertIn(
            "docs/architecture/connection-injection-contract.md",
            manifest["shared_paths"],
        )

    def test_peer_manifest_must_be_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            local = self._fixture(parent, "local")
            peer = self._fixture(parent, "peer")
            manifest = self._manifest(peer)
            manifest["mode"] = "unsafe"
            self._write_manifest(peer, manifest)

            with self.assertRaisesRegex(VALIDATOR.ContractError, "mode must be"):
                VALIDATOR.validate_contract(local, peer_root=peer)

    def test_contract_version_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(VALIDATOR.ContractError, "contract version mismatch"):
            VALIDATOR.validate_contract(ROOT, expected_contract_version=3)

    def test_source_sha_and_manifest_digest_are_bound(self) -> None:
        valid = VALIDATOR.validate_contract(ROOT)
        with self.assertRaisesRegex(VALIDATOR.ContractError, "full lowercase commit SHA"):
            VALIDATOR.validate_contract(
                ROOT,
                source_repository="flytohub/flyto-flow",
                source_sha="main",
            )
        with self.assertRaisesRegex(VALIDATOR.ContractError, "dispatched digest"):
            VALIDATOR.validate_contract(
                ROOT,
                expected_manifest_sha256="0" * 64,
            )
        rebound = VALIDATOR.validate_contract(
            ROOT,
            source_repository="flytohub/flyto-flow",
            source_sha="a" * 40,
            expected_manifest_sha256=valid["manifestSha256"],
        )
        self.assertEqual(rebound["sourceSha"], "a" * 40)

    def test_unsafe_and_missing_shared_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._fixture(Path(temp), "local")
            manifest = self._manifest(root)
            manifest["shared_paths"].append("../private-key")
            self._write_manifest(root, manifest)

            with self.assertRaisesRegex(VALIDATOR.ContractError, "unsafe shared path"):
                VALIDATOR.validate_contract(root)

    def test_manifest_sections_fail_closed(self) -> None:
        cases = [
            ("schema", "unsupported", "schema must be"),
            ("forbidden_cloud_to_flow_markers", ["Firebase"], "must be lowercase"),
            ("required_gates", [], "required_gates must be an object"),
            ("license_policy", [], "license_policy must be an object"),
        ]
        for field, value, expected_error in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = self._fixture(Path(temp), "local")
                manifest = self._manifest(root)
                manifest[field] = value
                self._write_manifest(root, manifest)

                with self.assertRaisesRegex(VALIDATOR.ContractError, expected_error):
                    VALIDATOR.validate_contract(root)

    def test_candidate_diff_must_exactly_match_selected_allowlisted_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            candidate = parent / "candidate.txt"
            expected = parent / "expected.txt"
            candidate.write_text("src/ui/web/frontend/src/api/mcp.js\n", encoding="utf-8")
            expected.write_text("src/ui/web/frontend/src/features/mcp/studio.css\n", encoding="utf-8")

            with self.assertRaisesRegex(VALIDATOR.ContractError, "exactly match"):
                VALIDATOR.validate_contract(
                    ROOT,
                    candidate_paths=candidate,
                    expected_paths=expected,
                )
            candidate.write_text("private/hosted.py\n", encoding="utf-8")
            with self.assertRaisesRegex(VALIDATOR.ContractError, "outside the allowlist"):
                VALIDATOR.validate_contract(ROOT, candidate_paths=candidate)


if __name__ == "__main__":
    unittest.main()
