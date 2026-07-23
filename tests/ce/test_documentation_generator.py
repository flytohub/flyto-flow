"""Regression tests for exact source-reference generation."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "flow_documentation_generator",
    ROOT / "scripts" / "generate_documentation_reference.py",
)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def test_javascript_symbol_lines_do_not_consume_blank_lines() -> None:
    symbols = GENERATOR.javascript_symbols("\n\nfunction start() {}\nclass Runner {}\n")

    assert ("function", "start()", 3) in symbols
    assert ("class", "Runner", 4) in symbols


def test_python_symbols_include_nested_classes_and_methods() -> None:
    tree = ast.parse(
        "def build():\n"
        "    class Handler:\n"
        "        def run(self):\n"
        "            return True\n"
    )

    rows, _ = GENERATOR.python_symbols(tree, "service.py")

    links = [row[1] for row in rows]
    assert any("service.py#L1" in link for link in links)
    assert any("service.py#L2" in link for link in links)
    assert any("service.py#L3" in link for link in links)


def test_rust_symbols_include_types_and_exact_function_lines() -> None:
    symbols = GENERATOR.rust_symbols("\nstruct Config {}\n\nimpl Config {\n    fn load() {}\n}\n")

    assert ("type", "Config", 2) in symbols
    assert ("function", "load()", 5) in symbols
