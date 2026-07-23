#!/usr/bin/env python3
"""Generate source-backed Flow API, frontend, route, and config references."""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference"
PYTHON_OUTPUT = REFERENCE / "python-api.md"
FRONTEND_OUTPUT = REFERENCE / "frontend-inventory.md"
ROUTES_OUTPUT = REFERENCE / "api-routes.md"
ENV_OUTPUT = REFERENCE / "environment.md"

PYTHON_ROOTS = (
    "src/ui/web/backend/",
    "scripts/",
)
FRONTEND_ROOTS = (
    "src/ui/web/frontend/",
    "scripts/",
)
HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put"}
TEST_MARKERS = ("/tests/", "/test/", "/e2e/", "__tests__", ".spec.", ".test.")
SECRET_MARKERS = ("API_KEY", "AUTH", "CREDENTIAL", "PASSWORD", "PRIVATE", "SECRET", "TOKEN")

JS_FUNCTION = re.compile(
    r"^(?P<indent>[ \t]*)(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\((?P<args>[^)]*)\)",
    re.MULTILINE,
)
JS_ARROW = re.compile(
    r"^(?P<indent>[ \t]*)(?:export\s+)?(?:const|let|var)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?"
    r"(?P<args>\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
    re.MULTILINE,
)
JS_METHOD = re.compile(
    r"^(?P<indent>[ \t]+)(?:async\s+)?(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"\((?P<args>[^)]*)\)\s*\{",
    re.MULTILINE,
)
JS_CLASS = re.compile(
    r"^[ \t]*(?:export\s+)?(?:default\s+)?class\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
ENV_PATTERNS = (
    re.compile(r"os\.(?:getenv|environ\.get)\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"os\.environ\[\s*['\"]([A-Z][A-Z0-9_]*)['\"]\s*\]"),
    re.compile(r"(?:process|import\.meta)\.env\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"env::var\(\s*['\"]([A-Z][A-Z0-9_]*)['\"]"),
)


def tracked_files() -> list[str]:
    """Return Git-tracked paths so generated and dependency trees stay excluded."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(result.stdout.splitlines())


def is_test(path: str) -> bool:
    """Return whether a path is test-only rather than a production surface."""
    lowered = f"/{path.lower()}"
    name = Path(path).name.lower()
    return any(marker in lowered for marker in TEST_MARKERS) or name.startswith("test_")


def humanize(name: str) -> str:
    """Create a stable plain-language fallback for undocumented symbols."""
    cleaned = name.strip("_").replace("$", " ").replace("_", " ") or name
    cleaned = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", cleaned)
    return " ".join(cleaned.split()).lower()


def generated_purpose(name: str, scope: str) -> str:
    """Describe an undocumented symbol from its action-oriented identifier."""
    words = humanize(name)
    parts = words.split(maxsplit=1)
    verb = parts[0]
    if len(parts) > 1:
        subject = parts[1]
    elif verb == "main":
        subject = "entry point"
    else:
        subject = f"`{name}` operation"
    actions = {
        "add": "Add",
        "apply": "Apply",
        "build": "Build",
        "calculate": "Calculate",
        "check": "Check",
        "clean": "Clean",
        "clear": "Clear",
        "collect": "Collect",
        "convert": "Convert",
        "create": "Create",
        "delete": "Delete",
        "dispatch": "Dispatch",
        "emit": "Emit",
        "ensure": "Ensure",
        "export": "Export",
        "extract": "Extract",
        "fetch": "Fetch",
        "filter": "Filter",
        "find": "Find",
        "format": "Format",
        "generate": "Generate",
        "get": "Return",
        "handle": "Handle",
        "import": "Import",
        "list": "List",
        "load": "Load",
        "main": "Run",
        "mark": "Mark",
        "normalize": "Normalize",
        "parse": "Parse",
        "publish": "Publish",
        "read": "Read",
        "remove": "Remove",
        "render": "Render",
        "request": "Request",
        "resolve": "Resolve",
        "run": "Run",
        "save": "Save",
        "send": "Send",
        "set": "Set",
        "start": "Start",
        "stop": "Stop",
        "track": "Track",
        "transform": "Transform",
        "update": "Update",
        "validate": "Validate",
        "verify": "Verify",
        "write": "Write",
    }
    if verb in {"can", "has", "is", "should"}:
        return f"Determine whether {subject} applies in `{scope}`."
    action = actions.get(verb)
    if action:
        return f"{action} {subject} for `{scope}`."
    return f"Implement the {words} operation for `{scope}`."


def first_sentence(doc: Optional[str], name: str, scope: str) -> str:
    """Return a compact source docstring or a deterministic role description."""
    if doc:
        flattened = " ".join(doc.strip().splitlines())
        return flattened.split(". ", 1)[0].rstrip(".") + "."
    return generated_purpose(name, scope)


def annotation(node: Optional[ast.expr]) -> str:
    """Render one Python type annotation."""
    return ast.unparse(node) if node is not None else ""


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef, *, method: bool) -> str:
    """Render a Python function signature without its body."""
    args = node.args
    parts: list[str] = []
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for arg, default in zip(positional, defaults):
        if method and arg.arg in {"self", "cls"}:
            continue
        value = arg.arg
        if arg.annotation:
            value += f": {annotation(arg.annotation)}"
        if default is not None:
            value += f" = {ast.unparse(default)}"
        parts.append(value)
    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        parts.append("*")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        value = arg.arg
        if arg.annotation:
            value += f": {annotation(arg.annotation)}"
        if default is not None:
            value += f" = {ast.unparse(default)}"
        parts.append(value)
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    result = f"{prefix}{node.name}({', '.join(parts)})"
    if node.returns:
        result += f" -> {annotation(node.returns)}"
    return result


def escaped(value: str) -> str:
    """Escape one value for a compact Markdown table cell."""
    return " ".join(value.split()).replace("|", "\\|")


def source_link(path: str, line: int, label: str) -> str:
    """Create a reference-document link to a source line."""
    return f"[`{escaped(label)}`](../../{path}#L{line})"


def python_files(files: Iterable[str]) -> Iterable[str]:
    """Yield production Python paths owned by Flow and maintenance scripts."""
    for path in files:
        if path.endswith(".py") and path.startswith(PYTHON_ROOTS) and not is_test(path):
            yield path


def python_symbols(tree: ast.Module, path: str) -> tuple[list[tuple[str, str, str, str]], int]:
    """Return classes and callables at every nesting level with exact source lines."""
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    rows: list[tuple[str, str, str, str]] = []
    undocumented = 0
    nodes = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            undocumented += not bool(doc)
            bases = ", ".join(ast.unparse(base) for base in node.bases)
            declaration = f"class {node.name}" + (f"({bases})" if bases else "")
            rows.append(
                (
                    "class",
                    source_link(path, node.lineno, node.name),
                    declaration,
                    first_sentence(doc, node.name, path),
                )
            )
            continue

        parent = parents.get(node)
        owner = parent.name if isinstance(parent, ast.ClassDef) else ""
        doc = ast.get_docstring(node)
        undocumented += not bool(doc)
        label = f"{owner}.{node.name}" if owner else node.name
        kind = "method" if owner else "function"
        if node.name.startswith("_"):
            kind = f"internal {kind}"
        rows.append(
            (
                kind,
                source_link(path, node.lineno, label),
                signature(node, method=bool(owner)),
                first_sentence(doc, node.name, owner or path),
            )
        )
    return rows, undocumented


def render_python(files: list[str]) -> tuple[str, int, int]:
    """Render every production Python class, function, and method."""
    lines = [
        "# Python API And Method Reference",
        "",
        "> Generated by `python scripts/generate_documentation_reference.py`. Do not edit manually.",
        "",
        "This inventory includes public and internal production callables. Generated",
        "fallback descriptions identify the owning source area when no docstring exists.",
        "",
    ]
    symbol_count = 0
    undocumented = 0
    for path in python_files(files):
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        rows, missing_docs = python_symbols(tree, path)
        undocumented += missing_docs
        symbol_count += len(rows)
        if not rows:
            continue
        lines.extend(
            [
                f"## `{path}`",
                "",
                "| Kind | Symbol | Signature | Purpose |",
                "|---|---|---|---|",
            ]
        )
        for kind, symbol, declaration, purpose in rows:
            lines.append(
                f"| {kind} | {symbol} | `{escaped(declaration)}` | {escaped(purpose)} |"
            )
        lines.append("")
    lines[7:7] = [
        f"Inventory: **{symbol_count} callables** across production Python sources; "
        f"**{undocumented}** use generated ownership descriptions.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n", symbol_count, undocumented


def line_number(content: str, offset: int) -> int:
    """Return a one-based line number for a regex match offset."""
    return content.count("\n", 0, offset) + 1


def frontend_files(files: Iterable[str]) -> Iterable[str]:
    """Yield production frontend and maintenance-script source files."""
    extensions = {".js", ".mjs", ".rs", ".ts", ".vue"}
    for path in files:
        if Path(path).suffix in extensions and path.startswith(FRONTEND_ROOTS) and not is_test(path):
            yield path


def javascript_symbols(content: str) -> list[tuple[str, str, int]]:
    """Extract named JavaScript/Vue callables without evaluating source code."""
    found: dict[tuple[str, int], tuple[str, str, int]] = {}
    for pattern, kind in ((JS_FUNCTION, "function"), (JS_ARROW, "arrow"), (JS_METHOD, "method")):
        for match in pattern.finditer(content):
            name = match.group("name")
            if name in {"catch", "for", "if", "switch", "while", "with"}:
                continue
            args = " ".join(match.group("args").split())
            line = line_number(content, match.start())
            found[(name, line)] = (kind, f"{name}({args.strip('()')})", line)
    for match in JS_CLASS.finditer(content):
        name = match.group("name")
        line = line_number(content, match.start())
        found[(name, line)] = ("class", name, line)
    return [found[key] for key in sorted(found, key=lambda item: (item[1], item[0]))]


def rust_symbols(content: str) -> list[tuple[str, str, int]]:
    """Extract named Rust types and functions from desktop source."""
    function_pattern = re.compile(
        r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+"
        r"([A-Za-z_][\w]*)\s*\(([^)]*)\)",
        re.MULTILINE,
    )
    type_pattern = re.compile(
        r"^[ \t]*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+([A-Za-z_][\w]*)",
        re.MULTILINE,
    )
    found = [
        ("function", f"{match.group(1)}({' '.join(match.group(2).split())})", line_number(content, match.start()))
        for match in function_pattern.finditer(content)
    ]
    found.extend(
        ("type", match.group(1), line_number(content, match.start()))
        for match in type_pattern.finditer(content)
    )
    return sorted(found, key=lambda item: (item[2], item[1]))


def render_frontend(files: list[str]) -> tuple[str, int, int]:
    """Render every production component/file and its named callables."""
    lines = [
        "# Frontend Source Inventory",
        "",
        "> Generated by `python scripts/generate_documentation_reference.py`. Do not edit manually.",
        "",
        "Every production Vue, JavaScript, and TypeScript source file is listed.",
        "Named declarations are indexed for direct source navigation.",
        "",
    ]
    file_count = 0
    callable_count = 0
    for path in frontend_files(files):
        file_count += 1
        content = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        symbols = rust_symbols(content) if path.endswith(".rs") else javascript_symbols(content)
        callable_count += len(symbols)
        role = "Vue component" if path.endswith(".vue") else "source module"
        lines.extend(
            [
                f"## [`{path}`](../../{path})",
                "",
                f"{role.capitalize()} for **{humanize(Path(path).stem)}**.",
                "",
            ]
        )
        if symbols:
            lines.extend(["| Kind | Callable | Purpose |", "|---|---|---|"])
            for kind, declaration, line in symbols:
                name = declaration.split("(", 1)[0]
                lines.append(
                    f"| {kind} | {source_link(path, line, declaration)} | "
                    f"{generated_purpose(name, Path(path).name)} |"
                )
            lines.append("")
    lines[7:7] = [
        f"Inventory: **{file_count} source files** and **{callable_count} named callables**.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n", file_count, callable_count


def string_value(node: ast.AST) -> Optional[str]:
    """Return a static string value when an AST node is literal."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def router_prefixes(tree: ast.Module) -> dict[str, str]:
    """Map local APIRouter variables to statically declared prefixes."""
    prefixes: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        function = value.func
        name = function.id if isinstance(function, ast.Name) else getattr(function, "attr", "")
        if name != "APIRouter":
            continue
        prefix = ""
        for keyword in value.keywords:
            if keyword.arg == "prefix":
                prefix = string_value(keyword.value) or "{dynamic-prefix}"
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                prefixes[target.id] = prefix
    return prefixes


def render_routes(files: list[str]) -> tuple[str, int]:
    """Render statically declared FastAPI/Starlette route decorators."""
    rows = []
    for path in python_files(files):
        if "/api/" not in path and not Path(path).name.startswith("main"):
            continue
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
        prefixes = router_prefixes(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr.lower()
                if method not in HTTP_METHODS or not decorator.args:
                    continue
                route = string_value(decorator.args[0])
                if route is None:
                    route = "{dynamic-path}"
                owner = decorator.func.value
                router = owner.id if isinstance(owner, ast.Name) else ""
                full_route = f"{prefixes.get(router, '')}{route}" or "/"
                rows.append(
                    (
                        full_route,
                        method.upper(),
                        node.name,
                        first_sentence(ast.get_docstring(node), node.name, path),
                        path,
                        node.lineno,
                    )
                )
    rows.sort(key=lambda item: (item[0], item[1], item[4], item[5]))
    lines = [
        "# API Route Reference",
        "",
        "> Generated by `python scripts/generate_documentation_reference.py`. Do not edit manually.",
        "",
        "Routes are extracted from static FastAPI/Starlette decorators. Prefixes created",
        "outside the defining module remain explicit as `{dynamic-prefix}`.",
        "",
        f"Inventory: **{len(rows)} route declarations**.",
        "",
        "| Method | Path | Handler | Purpose |",
        "|---|---|---|---|",
    ]
    for route, method, handler, purpose, path, line in rows:
        lines.append(
            f"| `{method}` | `{escaped(route)}` | {source_link(path, line, handler)} | "
            f"{escaped(purpose)} |"
        )
    return "\n".join(lines).rstrip() + "\n", len(rows)


def render_environment(files: list[str]) -> tuple[str, int]:
    """Render literal environment-variable reads with source ownership."""
    references: dict[str, set[str]] = defaultdict(set)
    extensions = {".js", ".mjs", ".py", ".rs", ".ts", ".vue"}
    for path in files:
        if Path(path).suffix not in extensions or is_test(path):
            continue
        content = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        for pattern in ENV_PATTERNS:
            for match in pattern.finditer(content):
                references[match.group(1)].add(path)
    lines = [
        "# Environment Reference",
        "",
        "> Generated by `python scripts/generate_documentation_reference.py`. Do not edit manually.",
        "",
        "This catalog lists literal environment-variable reads. Values and defaults remain",
        "owned by edition-specific `.env.example` files and configuration modules.",
        "",
        f"Inventory: **{len(references)} variables**.",
        "",
        "| Variable | Sensitive | Purpose | Source areas |",
        "|---|---|---|---|",
    ]
    for name, paths in sorted(references.items()):
        sensitive = "yes" if any(marker in name for marker in SECRET_MARKERS) else "no"
        sources = "<br>".join(f"[`{path}`](../../{path})" for path in sorted(paths))
        lines.append(
            f"| `{name}` | {sensitive} | {humanize(name)} configuration. | {sources} |"
        )
    return "\n".join(lines).rstrip() + "\n", len(references)


def main() -> int:
    """Write generated references or fail when committed outputs are stale."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = tracked_files()
    python_doc, python_count, undocumented = render_python(files)
    frontend_doc, frontend_files_count, frontend_callables = render_frontend(files)
    routes_doc, route_count = render_routes(files)
    env_doc, env_count = render_environment(files)
    outputs = {
        PYTHON_OUTPUT: python_doc,
        FRONTEND_OUTPUT: frontend_doc,
        ROUTES_OUTPUT: routes_doc,
        ENV_OUTPUT: env_doc,
    }
    if args.check:
        stale = [
            path.relative_to(ROOT).as_posix()
            for path, content in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print(f"stale documentation references: {', '.join(stale)}", file=sys.stderr)
            return 1
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    print(
        "documentation inventory: "
        f"python={python_count} (fallback={undocumented}), "
        f"frontend_files={frontend_files_count}, frontend_callables={frontend_callables}, "
        f"routes={route_count}, env={env_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
